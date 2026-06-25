import re

with open('backend/app/seed_data.py', 'r') as f:
    seed_data_content = f.read()

with open('backend/app/seed.py', 'r') as f:
    seed_content = f.read()

# Add categories
cat_addition = """    {"name": "SCH 80 Fittings", "slug": "sch-80-fittings", "parent_slug": "plumbing"},
    {"name": "Brass Fittings", "slug": "brass-fittings", "parent_slug": "plumbing"},"""
if "sch-80-fittings" not in seed_content:
    seed_content = seed_content.replace('{"name": "GI Fittings", "slug": "gi-fittings", "parent_slug": "plumbing"},',
        '{"name": "GI Fittings", "slug": "gi-fittings", "parent_slug": "plumbing"},\n' + cat_addition)

# Replace PRODUCTS
seed_content = re.sub(r'PRODUCTS = \[\s*(?:.|\n)*?\]\n', seed_data_content + '\n', seed_content, count=1)

# Add image seeding
image_seeding_code = """        # Variants
        for v in p.get("variants", []):"""

image_seeding_replacement = """        # Image
        if p.get("image"):
            await db.execute(
                text(\"\"\"
                    INSERT INTO product_images (product_id, image_url, is_primary, display_order)
                    VALUES (:pid, :img, TRUE, 0)
                \"\"\"),
                {"pid": product_id, "img": p["image"]},
            )

        # Variants
        for v in p.get("variants", []):"""

if "INSERT INTO product_images" not in seed_content:
    seed_content = seed_content.replace(image_seeding_code, image_seeding_replacement)

with open('backend/app/seed.py', 'w') as f:
    f.write(seed_content)
