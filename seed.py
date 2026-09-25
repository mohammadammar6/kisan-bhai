from app import create_app
from app.extensions import db
from app.models import Crop, CultivationStep, Irrigation, CropAdvice

CROPS = [
    {
        "name": "Paddy",
        "scientific_name": "Oryza sativa",
        "emoji": "🌾",
        "description": "Rice is commonly grown under flooded or carefully managed wet conditions. Timing and water management depend strongly on region and variety.",
        "soil": "Clay loam to loam soils with good water-holding capacity are commonly suitable.",
        "climate": "Warm conditions with adequate water; exact varieties and timing should follow local recommendations.",
        "sowing_period": "Varies by region and season; Kharif sowing/transplanting is common in much of India.",
        "harvest_period": "Usually about 100–150 days depending on variety and method.",
        "steps": [
            ("Land Preparation", "Prepare a level field with good bunds and drainage. Puddle where recommended for transplanted rice.", 1, 10),
            ("Nursery / Seed", "Use quality seed and a locally recommended variety. Establish a healthy nursery for transplanted systems.", 2, 25),
            ("Transplanting", "Transplant healthy seedlings at recommended age and spacing for the chosen variety.", 3, 1),
            ("Irrigation", "Maintain appropriate soil moisture or shallow standing water according to crop stage and local water-management practice.", 4, 100),
            ("Nutrients", "Apply nutrients based on soil testing and local recommendations; avoid blanket over-application of nitrogen.", 5, 100),
            ("Weed & Pest Monitoring", "Scout regularly for weeds, stem borers, planthoppers, blast and other locally prevalent problems.", 6, 100),
            ("Harvest", "Harvest when grains reach the recommended maturity and moisture level for the variety.", 7, 1),
        ],
        "irrigation": [
            ("Establishment", "Frequent checks", "Keep soil adequately moist", "Avoid prolonged drying immediately after establishment."),
            ("Vegetative", "As needed", "Maintain appropriate moisture", "Use local alternate wetting/drying guidance where suitable."),
            ("Reproductive", "Regular monitoring", "Avoid moisture stress", "This stage is sensitive to water stress."),
        ],
    },
    {
        "name": "Corn / Maize",
        "scientific_name": "Zea mays",
        "emoji": "🌽",
        "description": "Maize is a warm-season cereal requiring good sunlight, drainage and timely moisture.",
        "soil": "Well-drained fertile loam to sandy loam with good organic matter.",
        "climate": "Warm growing conditions with adequate moisture and sunlight.",
        "sowing_period": "Season varies by region; follow local Kharif/Rabi maize recommendations.",
        "harvest_period": "Roughly 90–150 days depending on variety and purpose.",
        "steps": [
            ("Land Preparation", "Prepare a fine, well-drained seedbed and incorporate organic matter where appropriate.", 1, 7),
            ("Sowing", "Use certified seed and maintain recommended row and plant spacing for the hybrid/variety.", 2, 1),
            ("Early Growth", "Control weeds early because maize is sensitive to competition during establishment.", 3, 30),
            ("Irrigation", "Provide moisture during establishment, rapid vegetative growth, tasseling and grain filling.", 4, 90),
            ("Nutrients", "Split nitrogen according to soil test and local recommendations; place fertilizer safely away from seed.", 5, 90),
            ("Pest Monitoring", "Scout for fall armyworm and other locally important pests; use integrated pest management.", 6, 100),
            ("Harvest", "Harvest when grain reaches appropriate maturity and moisture for the intended use.", 7, 1),
        ],
        "irrigation": [
            ("Establishment", "Light and regular", "Keep seed zone moist", "Avoid waterlogging."),
            ("Tasseling", "Regular", "Prevent moisture stress", "Critical moisture-sensitive stage."),
            ("Grain Filling", "As needed", "Maintain adequate moisture", "Adjust for rainfall and soil type."),
        ],
    },
    {
        "name": "Potato",
        "scientific_name": "Solanum tuberosum",
        "emoji": "🥔",
        "description": "Potato is a cool-season tuber crop that needs loose soil, drainage and careful irrigation.",
        "soil": "Loose, fertile, well-drained sandy loam to loam.",
        "climate": "Cool to mild temperatures; avoid prolonged heat and waterlogging.",
        "sowing_period": "Usually cool-season planting; exact dates depend on region.",
        "harvest_period": "Approximately 75–120 days depending on variety.",
        "steps": [
            ("Land Preparation", "Prepare loose, friable soil and ensure good drainage before planting.", 1, 10),
            ("Seed Tuber", "Use healthy certified seed tubers and plant at recommended depth and spacing.", 2, 1),
            ("Earthing Up", "Earth up around plants as tubers develop to protect tubers from light and support growth.", 3, 45),
            ("Irrigation", "Keep moisture even but avoid waterlogging. Adjust frequency for soil and rainfall.", 4, 100),
            ("Disease Monitoring", "Watch for late blight and other locally prevalent diseases, especially during cool wet periods.", 5, 100),
            ("Harvest", "Allow skin to mature appropriately before harvest when intended for storage.", 6, 1),
        ],
        "irrigation": [
            ("Emergence", "Light irrigation as needed", "Even moisture", "Avoid saturated soil."),
            ("Tuber Initiation", "Regular monitoring", "Consistent moisture", "Avoid large moisture swings."),
            ("Maturity", "Reduce as appropriate", "Avoid excess water near harvest", "Follow local practice."),
        ],
    },
    {
        "name": "Onion",
        "scientific_name": "Allium cepa",
        "emoji": "🧅",
        "description": "Onion requires good drainage, balanced nutrients and consistent moisture during bulb development.",
        "soil": "Well-drained loam to sandy loam with good fertility.",
        "climate": "Moderate temperatures; exact planting season depends on day length and local variety.",
        "sowing_period": "Season varies by region; use locally recommended nursery and transplanting dates.",
        "harvest_period": "Often 100–150 days depending on variety and season.",
        "steps": [
            ("Nursery", "Raise healthy seedlings in a well-prepared nursery using quality seed.", 1, 45),
            ("Transplanting", "Transplant uniform seedlings at recommended spacing without burying the growing point.", 2, 1),
            ("Weeding", "Keep beds weed-free during early bulb development.", 3, 60),
            ("Irrigation", "Provide light, timely irrigation; avoid waterlogging and large moisture fluctuations.", 4, 120),
            ("Nutrients", "Use soil-test-based fertilizer and avoid excess late nitrogen that can delay maturity.", 5, 100),
            ("Harvest", "Harvest after tops mature and bulbs reach marketable size; cure properly before storage.", 6, 1),
        ],
        "irrigation": [
            ("Establishment", "Frequent light irrigation", "Keep root zone moist", "Avoid standing water."),
            ("Bulb Development", "Regular", "Consistent moisture", "Reduce stress during bulb enlargement."),
            ("Maturity", "Reduce/stop as recommended", "Allow field to dry", "Supports curing and storage quality."),
        ],
    },
    {
        "name": "Garlic",
        "scientific_name": "Allium sativum",
        "emoji": "🧄",
        "description": "Garlic is grown from cloves and benefits from fertile, well-drained soil and moderate moisture.",
        "soil": "Well-drained loam or sandy loam rich in organic matter.",
        "climate": "Cool to moderate conditions during vegetative development.",
        "sowing_period": "Usually planted in cool season; exact timing varies by region.",
        "harvest_period": "Approximately 120–180 days depending on variety.",
        "steps": [
            ("Land Preparation", "Prepare loose, fertile beds with good drainage and incorporate mature organic matter.", 1, 7),
            ("Clove Planting", "Select healthy cloves and plant with pointed end upward at recommended depth and spacing.", 2, 1),
            ("Irrigation", "Maintain even moisture during establishment and bulb formation.", 3, 120),
            ("Weeding", "Control weeds early to reduce competition for nutrients and moisture.", 4, 90),
            ("Disease Monitoring", "Inspect for fungal diseases and maintain drainage and field sanitation.", 5, 120),
            ("Harvest & Curing", "Harvest after foliage matures and cure bulbs in a dry, ventilated place.", 6, 1),
        ],
        "irrigation": [
            ("Establishment", "Light and regular", "Moist root zone", "Avoid standing water."),
            ("Bulb Formation", "Regular", "Consistent moisture", "Adjust to rainfall."),
            ("Pre-harvest", "Reduce", "Allow drying", "Supports curing."),
        ],
    },
    {
        "name": "Ginger",
        "scientific_name": "Zingiber officinale",
        "emoji": "🫚",
        "description": "Ginger is a rhizome crop that benefits from rich organic soil, partial shade where locally suitable, mulch and good drainage.",
        "soil": "Deep, loose, fertile, well-drained loam rich in organic matter.",
        "climate": "Warm and humid conditions with adequate rainfall or irrigation.",
        "sowing_period": "Often planted with the onset of monsoon in suitable regions.",
        "harvest_period": "Around 6–9 months depending on purpose and variety.",
        "steps": [
            ("Land Preparation", "Prepare raised beds/ridges with good drainage and incorporate well-decomposed organic matter.", 1, 10),
            ("Rhizome Planting", "Use healthy disease-free seed rhizomes and plant at recommended depth.", 2, 1),
            ("Mulching", "Apply organic mulch to conserve moisture and suppress weeds.", 3, 120),
            ("Irrigation", "Maintain adequate moisture but prevent waterlogging.", 4, 180),
            ("Earthing Up", "Earth up periodically where locally recommended to support rhizome development.", 5, 150),
            ("Harvest", "Harvest green ginger earlier or mature rhizomes later depending on intended use.", 6, 1),
        ],
        "irrigation": [
            ("Establishment", "Regular light irrigation", "Adequate moisture", "Avoid saturation."),
            ("Rhizome Development", "Regular", "Maintain moisture", "Mulch can reduce water loss."),
            ("Maturity", "Reduce as appropriate", "Avoid excessive moisture", "Depends on harvest purpose."),
        ],
    },
]

def seed():
    app = create_app()
    with app.app_context():
        if db.session.scalar(db.select(Crop).limit(1)):
            print("Crops already seeded.")
            return
        for data in CROPS:
            crop = Crop(
                name=data["name"],
                scientific_name=data["scientific_name"],
                emoji=data["emoji"],
                description=data["description"],
                soil=data["soil"],
                climate=data["climate"],
                sowing_period=data["sowing_period"],
                harvest_period=data["harvest_period"],
            )
            db.session.add(crop)
            db.session.flush()
            for title, description, sequence, duration in data["steps"]:
                db.session.add(CultivationStep(
                    crop_id=crop.id,
                    stage=title,
                    title=title,
                    description=description,
                    sequence=sequence,
                    duration_days=duration
                ))
            for stage, frequency, water, description in data["irrigation"]:
                db.session.add(Irrigation(
                    crop_id=crop.id,
                    growth_stage=stage,
                    frequency=frequency,
                    water_requirement=water,
                    description=description
                ))
            db.session.add(CropAdvice(
                crop_id=crop.id,
                condition="general",
                advice="Use local soil tests, crop variety recommendations and agricultural extension guidance for exact fertilizer and plant-protection decisions.",
                severity="info"
            ))
        db.session.commit()
        print("KISAN BHAI crop catalog seeded successfully.")

if __name__ == "__main__":
    seed()
