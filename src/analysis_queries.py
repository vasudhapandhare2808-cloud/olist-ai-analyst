import duckdb

con = duckdb.connect("olist.duckdb")


# 1. Orders by status
print("\n1. ORDERS BY STATUS")
print(
    con.execute("""
        SELECT
            order_status,
            COUNT(*) AS order_count
        FROM olist_orders_dataset
        GROUP BY order_status
        ORDER BY order_count DESC
    """).fetchdf()
)


# 2. Average review score
print("\n2. AVERAGE REVIEW SCORE")
print(
    con.execute("""
        SELECT
            ROUND(AVG(review_score), 2) AS average_review_score
        FROM olist_order_reviews_dataset
    """).fetchdf()
)


# 3. Top 5 product categories by items sold
print("\n3. TOP 5 CATEGORIES BY ITEMS SOLD")
print(
    con.execute("""
        SELECT
            t.product_category_name_english AS category,
            COUNT(*) AS items_sold
        FROM olist_order_items_dataset i
        JOIN olist_products_dataset p
            ON i.product_id = p.product_id
        JOIN product_category_name_translation t
            ON p.product_category_name = t.product_category_name
        GROUP BY category
        ORDER BY items_sold DESC
        LIMIT 5
    """).fetchdf()
)


# 4. Average delivery time
print("\n4. AVERAGE DELIVERY TIME")
print(
    con.execute("""
        SELECT
            ROUND(
                AVG(
                    DATE_DIFF(
                        'day',
                        order_purchase_timestamp,
                        order_delivered_customer_date
                    )
                ),
                2
            ) AS avg_delivery_days
        FROM olist_orders_dataset
        WHERE order_delivered_customer_date IS NOT NULL
    """).fetchdf()
)


# 5. Percentage of late deliveries
print("\n5. LATE DELIVERY RATE")
print(
    con.execute("""
        SELECT
            ROUND(
                100.0 * AVG(
                    CASE
                        WHEN order_delivered_customer_date >
                             order_estimated_delivery_date
                        THEN 1
                        ELSE 0
                    END
                ),
                2
            ) AS late_delivery_percentage
        FROM olist_orders_dataset
        WHERE order_delivered_customer_date IS NOT NULL
    """).fetchdf()
)


con.close()