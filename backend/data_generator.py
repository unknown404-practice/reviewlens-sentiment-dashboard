"""
ReviewLens Synthetic Dataset Generator
======================================
Generates a deterministic, realistic demonstration review dataset for development,
educational, and testing purposes without relying on external web extraction.
"""

from __future__ import annotations

from datetime import date, timedelta
import random
from typing import Any, Dict, List
import numpy as np
import pandas as pd

RANDOM_SEED = 42

PRODUCTS_BY_CATEGORY: dict[str, list[str]] = {
    "Electronics": [
        "UltraClean Noise-Cancelling Headphones",
        "ProGamer Wireless Mechanical Keyboard",
        "Vision4K Smart Streaming Dongle",
    ],
    "Home and Kitchen": [
        "AromaBreeze Stainless Steel Espresso Maker",
        "ChefMaster 8-Piece Japanese Knife Set",
        "PureAir HEPA Room Air Purifier",
    ],
    "Beauty and Personal Care": [
        "HydraGlow Hyaluronic Acid Facial Serum",
        "SilkTouch Ceramic Hair Straightener",
        "Botanical Herbals Rejuvenating Night Cream",
    ],
    "Books": [
        "Data Science from Scratch (2nd Edition)",
        "The Pragmatic Programmer: 20th Anniversary",
        "Designing Data-Intensive Applications",
    ],
    "Sports and Outdoors": [
        "TrailBlazer Lightweight Trekking Poles",
        "ApexFit Resistance Band Training Set",
        "HydroFlow Insulated Stainless Water Bottle",
    ],
}

# Rich varied sentence components to ensure each generated review is unique
OPENERS = [
    "I have been testing this {product} for several weeks now and",
    "Purchased the {product} recently after comparing several options,",
    "After extensive daily use of the {product},",
    "Regarding this {product},",
    "My hands-on experience with the {product} shows that",
    "Having ordered the {product} last month,",
    "We needed a reliable solution and chose the {product}, and",
    "To be completely honest about the {product},",
    "Here is my honest take on the {product}:",
    "I took a chance on the {product} and",
    "Right out of the packaging, the {product}",
    "After reading mixed feedback online, I tried the {product} and",
]

TIER_DETAILS: dict[str, list[dict[str, Any]]] = {
    "strong_positive": [
        {
            "title": "Absolutely phenomenal quality!",
            "body": "it completely exceeded every expectation. Superb craftsmanship, lightning-fast setup, and premium durability. Highly recommend to everyone!",
            "rating": 5,
        },
        {
            "title": "Best purchase of the year",
            "body": "it delivers flawless performance and is worth every single penny. It feels sturdy, elegant, and genuinely works as advertised. 10/10!",
            "rating": 5,
        },
        {
            "title": "Outstanding build and reliability",
            "body": "the attention to detail is truly impressive. Works brilliantly right out of the box and has made a noticeable improvement in our routine.",
            "rating": 5,
        },
        {
            "title": "Exceptional value and engineering",
            "body": "incredible reliability and fantastic support. You will certainly not regret buying this. Truly top tier in its category.",
            "rating": 5,
        },
        {
            "title": "Delighted with this purchase!",
            "body": "smooth operation, gorgeous finish, and effortless usability. Will definitely be purchasing more from this line.",
            "rating": 5,
        },
    ],
    "moderate_positive": [
        {
            "title": "Very solid product with minor flaws",
            "body": "it performs well for day-to-day tasks. The build is respectable, although the included instructions could have been slightly clearer.",
            "rating": 4,
        },
        {
            "title": "Good quality for the price",
            "body": "the materials feel decent and it does its job smoothly. Delivery was fast and packaging was secure. Overall quite satisfied.",
            "rating": 4,
        },
        {
            "title": "Satisfied with this buy",
            "body": "good functionality and nice aesthetic. A few minor plastic components, but functionally it works very well.",
            "rating": 4,
        },
        {
            "title": "Decent performance overall",
            "body": "pleasantly surprised by how well it held up over a couple of weeks of daily usage. Would recommend for standard needs.",
            "rating": 4,
        },
        {
            "title": "Dependable and practical",
            "body": "works as expected with consistent results. A slight learning curve at first, but smooth sailing afterwards.",
            "rating": 4,
        },
    ],
    "neutral": [
        {
            "title": "Average, meets basic expectations",
            "body": "it arrived in standard packaging on schedule. Neither particularly impressed nor disappointed. It functions normally.",
            "rating": 3,
        },
        {
            "title": "Acceptable for standard use",
            "body": "a standard item that matches the product description. Nothing fancy, but serves as an acceptable baseline option.",
            "rating": 3,
        },
        {
            "title": "It is okay for the price",
            "body": "the product arrived as described. It is okay for the price, though there are better alternatives if you spend slightly more.",
            "rating": 3,
        },
        {
            "title": "Ordinary product without highlights",
            "body": "does what it says on the box. No major competitive advantages and no catastrophic failures either.",
            "rating": 3,
        },
    ],
    "moderate_negative": [
        {
            "title": "Somewhat underwhelming",
            "body": "I had higher hopes based on online claims. The performance is sluggish and build quality feels rather cheap for the price tag.",
            "rating": 2,
        },
        {
            "title": "Disappointing longevity",
            "body": "worked fine for the first two weeks, then started showing signs of wear and inconsistent behavior. Not really worth the hassle.",
            "rating": 2,
        },
        {
            "title": "Mediocre experience",
            "body": "flimsy construction and frustrating ergonomics. It technically works, but is unpleasant to use regularly.",
            "rating": 2,
        },
        {
            "title": "Below average quality",
            "body": "the finish peeled slightly and response times are slow. Would suggest looking at competitors instead.",
            "rating": 2,
        },
    ],
    "strong_negative": [
        {
            "title": "Complete waste of money",
            "body": "terrible product. It stopped working after one day and support was completely unhelpful. Avoid at all costs!",
            "rating": 1,
        },
        {
            "title": "Horrible quality and defective",
            "body": "extremely dissatisfied. Defective parts, awful customer service, and refusing to honor the warranty. Total disaster.",
            "rating": 1,
        },
        {
            "title": "Do not buy this!",
            "body": "total junk. Smelled strange, failed within minutes, and caused endless headaches trying to get a refund.",
            "rating": 1,
        },
        {
            "title": "Unusable and frustrating",
            "body": "terrible quality control. Began overheating immediately and made strange noises. Disgraceful standard.",
            "rating": 1,
        },
    ],
    "mixed": [
        {
            "title": "Great hardware but dreadful software",
            "body": "the physical hardware is sleek, beautifully engineered, and premium. Unfortunately the companion app crashes constantly and ruins the experience.",
            "rating": 3,
        },
        {
            "title": "Loved the design, hated the durability",
            "body": "looks gorgeous on my counter and received compliments, but unfortunately it broke down after only three weeks of light use.",
            "rating": 2,
        },
        {
            "title": "Difficult setup but great once working",
            "body": "customer service was unhelpful and instructions were missing, but once I finally got it configured, performance was outstanding.",
            "rating": 4,
        },
    ],
}


def generate_synthetic_reviews(target_count: int = 210, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate a deterministic synthetic reviews DataFrame with realistic variations,
    controlled data quality anomalies for cleaning demonstration, and verified schema.

    Args:
        target_count: Target number of base reviews (default: 210).
        seed: Random seed for reproducibility.

    Returns:
        pd.DataFrame adhering to the Phase 1 raw schema.
    """
    rng = np.random.default_rng(seed)
    py_random = random.Random(seed)

    categories = list(PRODUCTS_BY_CATEGORY.keys())
    sentiment_types = list(TIER_DETAILS.keys())
    sentiment_weights = [0.32, 0.25, 0.15, 0.14, 0.10, 0.04]

    records: list[dict[str, Any]] = []
    base_date = date(2025, 1, 15)

    for i in range(1, target_count + 1):
        review_id = f"DEMO-{i:05d}"
        category = py_random.choice(categories)
        product = py_random.choice(PRODUCTS_BY_CATEGORY[category])

        sentiment_choice = rng.choice(sentiment_types, p=sentiment_weights)
        tier_list = TIER_DETAILS[sentiment_choice]
        template = py_random.choice(tier_list)
        opener = py_random.choice(OPENERS).format(product=product)

        title = template["title"]
        # Unique review text created by combining dynamic opener and body
        text = f"{opener} {template['body']} [Ref: ID-{i}]"
        rating = template["rating"]

        # Date within last 2 years
        days_offset = int(rng.integers(0, 600))
        review_date = (base_date + timedelta(days=days_offset)).isoformat()

        verified = bool(rng.choice([True, False], p=[0.82, 0.18]))
        helpful = int(rng.geometric(p=0.35) - 1) if rng.random() > 0.3 else 0

        # Inject realistic formatting anomalies on specific non-overlapping records
        if i % 30 == 0:
            text = f"<div><b>{title}</b>: {text} <br/><span>Verified buyer.</span></div>"
        elif i % 40 == 0:
            text = f"{text} Check out specs at https://example.com/demo-review-data for more."
        elif i % 25 == 0:
            text = f"   {text[:25]}    {text[25:]}   "
        elif i % 50 == 0:
            text = f"{text} Highly impressive quality!!!! Absolutely loved it????"

        records.append({
            "review_id": review_id,
            "product_name": product,
            "product_category": category,
            "source": "Demo Dataset",
            "source_url": "https://example.com/demo-review-data",
            "review_title": title,
            "review_text": text,
            "rating": rating,
            "review_date": review_date,
            "verified_purchase": verified,
            "helpful_votes": helpful,
            "ingestion_timestamp": "2026-09-14T10:00:00Z",
            "data_mode": "DEMO",
        })

    # Controlled intentional anomalies for cleaning & validation demonstration:
    # 1. Missing review titles
    records[5]["review_title"] = None
    records[12]["review_title"] = ""
    records[22]["review_title"] = np.nan

    # 2. Missing / NaN helpful votes
    records[8]["helpful_votes"] = None
    records[30]["helpful_votes"] = np.nan
    records[75]["helpful_votes"] = None

    # 3. Malformed / empty review texts (should be removed during cleaning)
    records[40]["review_text"] = "   "
    records[80]["review_text"] = None
    records[120]["review_text"] = "!!!"

    # 4. Invalid ratings (MUST be retained until rating validation to demonstrate removal)
    records[15]["rating"] = 0      # rating 0 (below 1)
    records[65]["rating"] = 6      # rating 6 (above 5)
    records[115]["rating"] = -1    # negative rating
    records[165]["rating"] = None  # missing rating

    # 5. Duplicate review texts (same text, different review_id)
    records[55]["review_text"] = records[10]["review_text"]
    records[95]["review_text"] = records[20]["review_text"]

    # 6. Fully duplicated rows (exact identical row cloned)
    duplicate_row_1 = dict(records[14])
    duplicate_row_2 = dict(records[28])
    records.append(duplicate_row_1)
    records.append(duplicate_row_2)

    df = pd.DataFrame(records)
    return df
