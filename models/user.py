import json
from database.db import get_db_connection
import cloudinary
import cloudinary.uploader
from datetime import datetime

class RMA:
    
    @staticmethod
    def generate_rma_number():
        conn = get_db_connection()
        cursor = conn.cursor()
        current_date = datetime.now().strftime("%m%d%Y")
        cursor.execute('''
            SELECT COUNT(*) FROM rma_requests 
            WHERE rma_number LIKE %s
        ''', (f'RMA-{current_date}-%',))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        sequence = str(count + 1).zfill(3)
        return f"RMA-{current_date}-{sequence}"
    
    @staticmethod
    def create(data, files=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        rma_number = RMA.generate_rma_number()
        
        # Kunin ang attachment_names galing sa form data
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
        
        attachments_json = json.dumps(attachment_urls) if attachment_urls else None
        
        try:
            cursor.execute('''
                INSERT INTO rma_requests (
                    rma_number, dealer_id,
                    return_type, reason_for_return, warranty,
                    filer_name, distributor_name, date_filled, product, product_description,
                    work_environment,
                    po_number, sales_invoice_number,
                    shipping_date, return_date,
                    end_user_company, end_user_location,
                    end_user_industry, end_user_contact_person,
                    problem_description, dealer_comments,
                    attachments, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                rma_number, int(data.get('dealer_id')),
                data.get('return_type'), data.get('reason_for_return'),
                1 if data.get('warranty') == 'true' or data.get('warranty') == True else 0,
                data.get('filer_name'), data.get('distributor_name'), data.get('date_filled'), data.get('product'), data.get('product_description'),
                data.get('work_environment'),
                data.get('po_number'), data.get('sales_invoice_number'),
                data.get('shipping_date'), data.get('return_date'),
                data.get('end_user_company'), data.get('end_user_location'),
                data.get('end_user_industry'), data.get('end_user_contact_person'),
                data.get('problem_description'), data.get('dealer_comments'),
                attachments_json, 'pending_authorizer'
            ))
            rma_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True, 'rma_id': rma_id, 'rma_number': rma_number, 'attachments': attachment_urls}
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_by_dealer(dealer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM rma_requests 
            WHERE dealer_id = %s 
            ORDER BY created_at DESC
        ''', (dealer_id,))
        rows = cursor.fetchall()
        rmas = []
        for row in rows:
            rma_dict = dict(row)
            if rma_dict.get('attachments'):
                rma_dict['attachments'] = json.loads(rma_dict['attachments'])
            rmas.append(rma_dict)
        cursor.close()
        conn.close()
        return rmas
    
    @staticmethod
    def get_by_id(rma_id, dealer_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        if dealer_id:
            cursor.execute('''
                SELECT * FROM rma_requests 
                WHERE id = %s AND dealer_id = %s
            ''', (rma_id, dealer_id))
        else:
            cursor.execute('SELECT * FROM rma_requests WHERE id = %s', (rma_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            rma_dict = dict(row)
            if rma_dict.get('attachments'):
                rma_dict['attachments'] = json.loads(rma_dict['attachments'])
            return rma_dict
        return None
    
    @staticmethod
    def update(rma_id, dealer_id, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT status FROM rma_requests 
            WHERE id = %s AND dealer_id = %s
        ''', (rma_id, dealer_id))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return {'success': False, 'error': 'RMA not found'}
        if row['status'] != 'pending_authorizer':
            cursor.close()
            conn.close()
            return {'success': False, 'error': 'Cannot edit - RMA already processed'}
        try:
            cursor.execute('''
                UPDATE rma_requests SET
                    return_type = %s, reason_for_return = %s, warranty = %s,
                    filer_name = %s, distributor_name = %s, date_filled = %s, product = %s, product_description = %s,
                    work_environment = %s,
                    po_number = %s, sales_invoice_number = %s,
                    shipping_date = %s, return_date = %s,
                    end_user_company = %s, end_user_location = %s,
                    end_user_industry = %s, end_user_contact_person = %s,
                    problem_description = %s, dealer_comments = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND dealer_id = %s
            ''', (
                data.get('return_type'), data.get('reason_for_return'),
                1 if data.get('warranty') else 0,
                data.get('filer_name'), data.get('distributor_name'), data.get('date_filled'), data.get('product'), data.get('product_description'),
                data.get('work_environment'),
                data.get('po_number'), data.get('sales_invoice_number'),
                data.get('shipping_date'), data.get('return_date'),
                data.get('end_user_company'), data.get('end_user_location'),
                data.get('end_user_industry'), data.get('end_user_contact_person'),
                data.get('problem_description'), data.get('dealer_comments'),
                rma_id, dealer_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete(rma_id, dealer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT status FROM rma_requests 
            WHERE id = %s AND dealer_id = %s
        ''', (rma_id, dealer_id))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return {'success': False, 'error': 'RMA not found'}
        if row['status'] != 'pending_authorizer':
            cursor.close()
            conn.close()
            return {'success': False, 'error': 'Cannot delete - RMA already processed'}
        try:
            # Delete attachments from Cloudinary
            cursor.execute('SELECT attachments FROM rma_requests WHERE id = %s', (rma_id,))
            row = cursor.fetchone()
            if row and row['attachments']:
                attachments = json.loads(row['attachments'])
                for att in attachments:
                    try:
                        cloudinary.uploader.destroy(att['public_id'])
                    except:
                        pass
            cursor.execute('DELETE FROM rma_requests WHERE id = %s AND dealer_id = %s', (rma_id, dealer_id))
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True}
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return {'success': False, 'error': str(e)}