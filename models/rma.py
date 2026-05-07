from database.db import get_db_connection
from datetime import datetime
from bson import ObjectId
import json
import cloudinary
import cloudinary.uploader

class RMA:
    
    @staticmethod
    def _serialize(doc):
        """Convert MongoDB document to dictionary with string id"""
        if doc:
            doc['id'] = str(doc.pop('_id'))
        return doc
    
    @staticmethod
    def generate_rma_number():
        """Generate unique RMA number: RMA-MMDDYYYY-XXX"""
        db = get_db_connection()
        current_date = datetime.now().strftime("%m%d%Y")
        
        # Count existing RMAs for today
        count = db.rma_requests.count_documents({
            "rma_number": {"$regex": f"RMA-{current_date}-"}
        })
        
        sequence = str(count + 1).zfill(3)
        return f"RMA-{current_date}-{sequence}"
    
    @staticmethod
    def create(data, files=None):
        """Create RMA request"""
        try:
            print("=" * 50)
            print("RMA.create called")
            print(f"Data received: {data}")
            
            # Check required fields
            required_fields = [
                'dealer_id', 'return_type', 'reason_for_return', 'filer_name',
                'distributor_name', 'date_filled', 'product', 'product_description',
                'work_environment', 'po_number', 'sales_invoice_number',
                'shipping_date', 'return_date', 'end_user_company', 'end_user_location',
                'end_user_industry', 'end_user_contact_person', 'problem_description',
                'dealer_comments'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    'success': False, 
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }
            
            db = get_db_connection()
            rma_number = RMA.generate_rma_number()
            
            # Handle attachments
            attachment_names = data.get('attachment_names', '[]')
            if isinstance(attachment_names, str):
                try:
                    attachment_names = json.loads(attachment_names)
                except:
                    attachment_names = []
            
            attachment_urls = []
            if files:
                for idx, file_data in enumerate(files):
                    try:
                        original_name = attachment_names[idx] if idx < len(attachment_names) else f"file_{idx+1}"
                        upload_result = cloudinary.uploader.upload(
                            file_data,
                            folder=f"rma_attachments/{rma_number}",
                            resource_type="auto",
                            use_filename=True,
                            unique_filename=False,
                            filename_override=original_name
                        )
                        attachment_urls.append({
                            'url': upload_result['secure_url'],
                            'public_id': upload_result['public_id'],
                            'resource_type': upload_result['resource_type'],
                            'format': upload_result.get('format', ''),
                            'bytes': upload_result.get('bytes', 0),
                            'original_filename': original_name,
                            'filename': original_name
                        })
                    except Exception as e:
                        print(f"Upload error: {e}")
            
            # Convert warranty to integer
            warranty_value = 1 if data.get('warranty') in ['true', 'True', True, 1, '1'] else 0
            
            # Create RMA document
            rma = {
                "rma_number": rma_number,
                "dealer_id": data.get('dealer_id'),
                "return_type": data.get('return_type'),
                "reason_for_return": data.get('reason_for_return'),
                "warranty": warranty_value,
                "filer_name": data.get('filer_name'),
                "distributor_name": data.get('distributor_name'),
                "date_filled": data.get('date_filled'),
                "product": data.get('product'),
                "product_description": data.get('product_description'),
                "work_environment": data.get('work_environment'),
                "po_number": data.get('po_number'),
                "sales_invoice_number": data.get('sales_invoice_number'),
                "shipping_date": data.get('shipping_date'),
                "return_date": data.get('return_date'),
                "end_user_company": data.get('end_user_company'),
                "end_user_location": data.get('end_user_location'),
                "end_user_industry": data.get('end_user_industry'),
                "end_user_contact_person": data.get('end_user_contact_person'),
                "problem_description": data.get('problem_description'),
                "dealer_comments": data.get('dealer_comments'),
                "attachments": attachment_urls,
                "authorized_by": None,
                "authorized_date": None,
                "return_received_by": None,
                "authorizer_comments": None,
                "authorizer_attachments": [],
                "approved_by": None,
                "approved_date": None,
                "approved_with": None,
                "replacement_order_no": None,
                "closed_date": None,
                "approver_comments": None,
                "approver_attachments": [],
                "status": "pending_authorizer",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            result = db.rma_requests.insert_one(rma)
            rma_id = str(result.inserted_id)
            
            print(f"RMA created successfully: {rma_number} (ID: {rma_id})")
            
            return {
                'success': True,
                'rma_id': rma_id,
                'rma_number': rma_number,
                'attachments': attachment_urls
            }
            
        except Exception as e:
            import traceback
            print(f"Error in RMA.create: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_by_dealer(dealer_id):
        """Get all RMAs for a specific dealer"""
        db = get_db_connection()
        rmas = list(db.rma_requests.find({"dealer_id": dealer_id}).sort("created_at", -1))
        return [RMA._serialize(r) for r in rmas]
    
    @staticmethod
    def get_by_id(rma_id, dealer_id=None):
        """Get RMA by ID (optionally check dealer_id)"""
        db = get_db_connection()
        try:
            query = {"_id": ObjectId(rma_id)}
            if dealer_id:
                query["dealer_id"] = dealer_id
            
            rma = db.rma_requests.find_one(query)
            return RMA._serialize(rma)
        except:
            return None
    
    @staticmethod
    def update(rma_id, dealer_id, data):
        """Update RMA request (only if pending_authorizer)"""
        db = get_db_connection()
        
        # Check if RMA exists and is pending
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id), "dealer_id": dealer_id})
        if not rma:
            return {'success': False, 'error': 'RMA not found'}
        
        if rma['status'] != 'pending_authorizer':
            return {'success': False, 'error': 'Cannot edit - RMA already processed'}
        
        # Prepare update data
        update_data = {
            "return_type": data.get('return_type'),
            "reason_for_return": data.get('reason_for_return'),
            "warranty": 1 if data.get('warranty') else 0,
            "filer_name": data.get('filer_name'),
            "distributor_name": data.get('distributor_name'),
            "date_filled": data.get('date_filled'),
            "product": data.get('product'),
            "product_description": data.get('product_description'),
            "work_environment": data.get('work_environment'),
            "po_number": data.get('po_number'),
            "sales_invoice_number": data.get('sales_invoice_number'),
            "shipping_date": data.get('shipping_date'),
            "return_date": data.get('return_date'),
            "end_user_company": data.get('end_user_company'),
            "end_user_location": data.get('end_user_location'),
            "end_user_industry": data.get('end_user_industry'),
            "end_user_contact_person": data.get('end_user_contact_person'),
            "problem_description": data.get('problem_description'),
            "dealer_comments": data.get('dealer_comments'),
            "updated_at": datetime.now()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {'success': True}
        return {'success': False, 'error': 'No changes made'}
    
    @staticmethod
    def delete(rma_id, dealer_id):
        """Delete RMA request (only if pending_authorizer)"""
        db = get_db_connection()
        
        # Check if RMA exists and is pending
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id), "dealer_id": dealer_id})
        if not rma:
            return {'success': False, 'error': 'RMA not found'}
        
        if rma['status'] != 'pending_authorizer':
            return {'success': False, 'error': 'Cannot delete - RMA already processed'}
        
        # Delete attachments from Cloudinary
        if rma.get('attachments'):
            for att in rma['attachments']:
                try:
                    if att.get('public_id'):
                        cloudinary.uploader.destroy(att['public_id'])
                except:
                    pass
        
        result = db.rma_requests.delete_one({"_id": ObjectId(rma_id)})
        
        if result.deleted_count > 0:
            return {'success': True}
        return {'success': False, 'error': 'Failed to delete'}
    
    @staticmethod
    def get_all():
        """Get all RMAs with dealer information"""
        db = get_db_connection()
        
        pipeline = [
            {"$addFields": {
                "dealer_id_obj": {
                    "$cond": [
                        {"$and": [
                            {"$ne": ["$dealer_id", None]},
                            {"$ne": ["$dealer_id", ""]},
                            {"$eq": [{"$type": "$dealer_id"}, "string"]}
                        ]},
                        {"$toObjectId": "$dealer_id"},
                        "$dealer_id"
                    ]
                }
            }},
            {"$lookup": {
                "from": "users",
                "localField": "dealer_id_obj",
                "foreignField": "_id",
                "as": "dealer"
            }},
            {"$unwind": {"path": "$dealer", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": "dealer_profiles",
                "localField": "dealer._id",
                "foreignField": "user_id",
                "as": "profile"
            }},
            {"$unwind": {"path": "$profile", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "company_name": { "$ifNull": ["$profile.company_name", "$distributor_name", "N/A"] }
            }},
            {"$sort": {"created_at": -1}}
        ]
        
        rmas = list(db.rma_requests.aggregate(pipeline))
        return [RMA._serialize(r) for r in rmas]

    @staticmethod
    def get_pending_for_authorizer():
        """Get all RMAs pending for authorizer with dealer info"""
        db = get_db_connection()
        pipeline = [
            {"$match": {"status": "pending_authorizer"}},
            {"$addFields": {
                "dealer_id_obj": {
                    "$cond": [
                        {"$and": [
                            {"$ne": ["$dealer_id", None]},
                            {"$ne": ["$dealer_id", ""]},
                            {"$eq": [{"$type": "$dealer_id"}, "string"]}
                        ]},
                        {"$toObjectId": "$dealer_id"},
                        "$dealer_id"
                    ]
                }
            }},
            {"$lookup": {
                "from": "users",
                "localField": "dealer_id_obj",
                "foreignField": "_id",
                "as": "dealer"
            }},
            {"$unwind": {"path": "$dealer", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": "dealer_profiles",
                "localField": "dealer._id",
                "foreignField": "user_id",
                "as": "profile"
            }},
            {"$unwind": {"path": "$profile", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "company_name": { "$ifNull": ["$profile.company_name", "$distributor_name", "N/A"] }
            }},
            {"$sort": {"created_at": 1}}
        ]
        rmas = list(db.rma_requests.aggregate(pipeline))
        return [RMA._serialize(r) for r in rmas]

    @staticmethod
    def get_pending_for_approver():
        """Get all RMAs pending for approver (authorized) with dealer info"""
        db = get_db_connection()
        pipeline = [
            {"$match": {"status": "authorized"}},
            {"$addFields": {
                "dealer_id_obj": {
                    "$cond": [
                        {"$and": [
                            {"$ne": ["$dealer_id", None]},
                            {"$ne": ["$dealer_id", ""]},
                            {"$eq": [{"$type": "$dealer_id"}, "string"]}
                        ]},
                        {"$toObjectId": "$dealer_id"},
                        "$dealer_id"
                    ]
                }
            }},
            {"$lookup": {
                "from": "users",
                "localField": "dealer_id_obj",
                "foreignField": "_id",
                "as": "dealer"
            }},
            {"$unwind": {"path": "$dealer", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": "dealer_profiles",
                "localField": "dealer._id",
                "foreignField": "user_id",
                "as": "profile"
            }},
            {"$unwind": {"path": "$profile", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "company_name": { "$ifNull": ["$profile.company_name", "$distributor_name", "N/A"] }
            }},
            {"$sort": {"authorized_date": 1}}
        ]
        rmas = list(db.rma_requests.aggregate(pipeline))
        return [RMA._serialize(r) for r in rmas]
    
    @staticmethod
    def authorize(rma_id, data):
        """Authorize an RMA (by authorizer)"""
        db = get_db_connection()
        
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id)})
        if not rma:
            return {'success': False, 'error': 'RMA not found'}
        
        if rma['status'] != 'pending_authorizer':
            return {'success': False, 'error': 'RMA is not pending for authorization'}
        
        update_data = {
            "authorized_by": data.get('authorized_by'),
            "authorized_date": data.get('authorized_date', datetime.now().strftime("%Y-%m-%d")),
            "return_date": data.get('return_date'),
            "return_received_by": data.get('return_received_by'),
            "authorizer_comments": data.get('authorizer_comments'),
            "status": "authorized",
            "updated_at": datetime.now()
        }
        
        # Handle attachments if any
        if data.get('authorizer_attachments'):
            update_data["authorizer_attachments"] = data.get('authorizer_attachments')
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {'success': True, 'status': 'authorized'}
        return {'success': False, 'error': 'No changes made'}
    
    @staticmethod
    def approve(rma_id, data):
        """Approve an RMA (by approver)"""
        db = get_db_connection()
        
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id)})
        if not rma:
            return {'success': False, 'error': 'RMA not found'}
        
        if rma['status'] != 'authorized':
            return {'success': False, 'error': 'RMA is not authorized'}
        
        update_data = {
            "approved_by": data.get('approved_by'),
            "approved_date": data.get('approved_date', datetime.now().strftime("%Y-%m-%d")),
            "approved_with": data.get('approved_with'),
            "replacement_order_no": data.get('replacement_order_no'),
            "closed_date": data.get('closed_date'),
            "approver_comments": data.get('approver_comments'),
            "status": "approved",
            "updated_at": datetime.now()
        }
        
        # Handle attachments if any
        if data.get('approver_attachments'):
            update_data["approver_attachments"] = data.get('approver_attachments')
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {'success': True, 'status': 'approved'}
        return {'success': False, 'error': 'No changes made'}
    
    @staticmethod
    def reject(rma_id, data, role):
        """Reject an RMA (by authorizer or approver)"""
        db = get_db_connection()
        
        rma = db.rma_requests.find_one({"_id": ObjectId(rma_id)})
        if not rma:
            return {'success': False, 'error': 'RMA not found'}
        
        if role == 'authorizer' and rma['status'] != 'pending_authorizer':
            return {'success': False, 'error': 'RMA is not pending for authorization'}
        
        if role == 'approver' and rma['status'] != 'authorized':
            return {'success': False, 'error': 'RMA is not authorized'}
        
        update_data = {
            "status": "rejected",
            "updated_at": datetime.now()
        }
        
        if role == 'authorizer':
            update_data["authorized_by"] = data.get('authorized_by')
            update_data["authorizer_comments"] = data.get('authorizer_comments')
        else:
            update_data["approved_by"] = data.get('approved_by')
            update_data["approver_comments"] = data.get('approver_comments')
        
        result = db.rma_requests.update_one(
            {"_id": ObjectId(rma_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return {'success': True, 'status': 'rejected'}
        return {'success': False, 'error': 'No changes made'}
    
    @staticmethod
    def get_stats():
        """Get RMA statistics"""
        db = get_db_connection()
        
        # Status counts
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        status_counts = {item['_id']: item['count'] for item in db.rma_requests.aggregate(pipeline)}
        
        return status_counts