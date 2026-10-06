from lagosdata.sources.site_contacts.extractors import extract_contacts

def test_contact_and_delivery_extraction():
    html='<a href="mailto:hello@shop.ng">Email</a><a href="https://wa.me/2348031234567">WhatsApp</a><a href="https://instagram.com/shop">Instagram</a>'
    data=extract_contacts(html,'We deliver bulk orders. Contact 0803 123 4567. Order online.','https://shop.ng/')
    assert data['emails']==['hello@shop.ng'] and data['whatsapp']=='+2348031234567'
    assert data['socials']['instagram']=='https://instagram.com/shop'
    assert data['phones']==['+2348031234567'] and data['online_order'] and data['delivery_signals']
