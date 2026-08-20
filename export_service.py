import csv
import io
from datetime import datetime

def export_inquiries_csv(inquiries):
    """
    Exports a list of inquiries to a CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Inquiry Ref #',
        'Date (UTC)',
        'Customer Name',
        'Company Name',
        'Email',
        'Phone',
        'Country',
        'Machine Model',
        'Status',
        'Product Name',
        'Part Number',
        'Quantity',
        'Item Notes',
        'Customer Message',
        'Admin Notes'
    ])
    
    for inq in inquiries:
        created_str = inq.created_at.strftime('%Y-%m-%d %H:%M') if inq.created_at else ''
        if inq.items:
            for item in inq.items:
                writer.writerow([
                    inq.inquiry_number,
                    created_str,
                    inq.customer_name,
                    inq.company_name or '',
                    inq.email,
                    inq.phone,
                    inq.country or '',
                    inq.machine_model or '',
                    inq.status,
                    item.product_name,
                    item.part_number or '',
                    item.quantity,
                    item.notes or '',
                    inq.message or '',
                    inq.admin_notes or ''
                ])
        else:
            writer.writerow([
                inq.inquiry_number,
                created_str,
                inq.customer_name,
                inq.company_name or '',
                inq.email,
                inq.phone,
                inq.country or '',
                inq.machine_model or '',
                inq.status,
                'General Inquiry',
                '',
                1,
                '',
                inq.message or '',
                inq.admin_notes or ''
            ])
            
    output.seek(0)
    return output.getvalue()


def export_products_csv(products):
    """
    Exports product catalog to CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID',
        'Part Number',
        'Product Name',
        'Category',
        'Machine Make',
        'Repeat Sizes',
        'Material',
        'Description',
        'Specifications',
        'Featured',
        'Active',
        'Created Date'
    ])
    
    for p in products:
        writer.writerow([
            p.id,
            p.part_number,
            p.name,
            p.category.name if p.category else '',
            p.machine_make.name if p.machine_make else 'Universal',
            p.repeat_sizes or '',
            p.material or '',
            p.description or '',
            p.specifications or '',
            'Yes' if p.is_featured else 'No',
            'Yes' if p.is_active else 'No',
            p.created_at.strftime('%Y-%m-%d') if p.created_at else ''
        ])
        
    output.seek(0)
    return output.getvalue()
