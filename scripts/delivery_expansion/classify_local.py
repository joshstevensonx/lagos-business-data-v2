import re
def classify(gcat, name, terms):
    """-> (delivery_category, group, subcategory, scorer_category_text) or None to drop."""
    g=(gcat or '').lower(); n=(name or '').lower(); t=' '.join(terms or []).lower(); blob=g+' '+n
    if re.search(r'pharmac|chemist|drug ?store|drugstore',blob): return 'Pharmacy','Health & Medical','Pharmacies','pharmacy'
    if re.search(r'hospital|clinic|diagnostic|laborator|dental|optical|spa\b|salon|hotel|school|church|bank|gym|lounge|night ?club|bar$|^bar\b|hostel|apartment|estate agent|real estate',g) and not re.search(r'restaurant|grill|food|cafe',g): return None
    if re.search(r'cater',g): return 'Catering','Catering & Events Food','Caterers','restaurant'
    if re.search(r'ice cream|gelato|frozen yogh?urt|yogh?urt',g): return 'Bakery / Desserts','Baking & Desserts','Ice Cream Shops','restaurant'
    if re.search(r'bakery|bakeries|pastry|patisserie|cake|bread|donut|doughnut|dessert|confection',g): return 'Bakery / Desserts','Baking & Desserts','Bakeries' if re.search(r'bakery|bread',g) else 'Pastry Shops','restaurant'
    if re.search(r'liquor|wine|off.?licen|beer|spirits|drinks|alcohol',g): return 'Drinks / Liquor','Retail & Groceries','Wine & Drinks Shops','other'
    if re.search(r'frozen|meat|butcher|fish|seafood market|poultry',g) and not re.search(r'restaurant',g): return 'Supermarket / Grocery','Retail & Groceries','Frozen Food Shops' if re.search(r'frozen|fish|poultry',g) else 'Meat Shops','supermarket'
    if re.search(r'supermarket|hypermarket|grocery|convenience|mini ?mart|market|provision|general store|variety store|greengrocer|department store|wholesale|food store|shopping mall',g):
        sub='Supermarkets' if re.search(r'supermarket|hypermarket|department|mall|wholesale',g) else 'Mini-Marts' if re.search(r'mini',g) else 'Convenience Stores' if 'convenience' in g else 'Provision Stores'
        return 'Supermarket / Grocery','Retail & Groceries',sub,'supermarket'
    if re.search(r'coffee|cafe|café|tea house|juice|smoothie',g): return 'Cafe / Coffee','Food & Restaurants','Coffee Shops' if 'coffee' in g else 'Cafes','restaurant'
    if re.search(r'restaurant|fast food|food|grill|diner|bistro|buka|bukka|canteen|eatery|pizza|burger|chicken|shawarma|suya|barbecue|steak|takeout|takeaway|kitchen|lunch|breakfast|bar & grill|sandwich|noodle|sushi|buffet',g) or (not g and re.search(r'restaurant|kitchen|grill|food|bukka|buka',n)):
        sub='Restaurants'
        for pat,s in [(r'pizza','Pizza Outlets'),(r'burger|hamburger','Burger Outlets'),(r'chicken','Chicken Shops'),(r'shawarma','Shawarma'),(r'suya','Suya'),(r'grill|barbecue|steak','Grills'),(r'seafood|fish','Seafood Restaurants'),(r'chinese|asian|thai|sushi|japanese|noodle|indian','Chinese/Asian Restaurants'),(r'buka|bukka','Buka'),(r'fast food|takeout|takeaway','Fast Food'),(r'west african|nigerian|african','Nigerian Restaurants'),(r'breakfast','Breakfast Outlets')]:
            if re.search(pat,g) or (s in('Buka',) and re.search(pat,n)): sub=s;break
        return 'Restaurant / Food','Food & Restaurants',sub,'restaurant'
    if g=='store' and re.search(r'grocery|provision|mini mart|supermarket|hypermarket',t): return 'Supermarket / Grocery','Retail & Groceries','Provision Stores','supermarket'
    # category unknown/other: fall back on which search term found it
    if not g:
        if re.search(r'pharmacy|chemist',t): return 'Pharmacy','Health & Medical','Pharmacies','pharmacy'
    return None
