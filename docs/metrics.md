# Olist Business Metrics

## 1. Total Orders

**Definition:** Number of unique orders in the Olist orders table.

**SQL logic:**
COUNT(*) from `olist_orders_dataset`

---

## 2. Average Review Score

**Definition:** Average customer review score across available reviews.

**SQL logic:**
AVG(`review_score`) from `olist_order_reviews_dataset`

**Current value:** 4.09 / 5

---

## 3. Items Sold by Category

**Definition:** Number of order items sold for each translated product category.

**Tables used:**
- `olist_order_items_dataset`
- `olist_products_dataset`
- `product_category_name_translation`

**Join path:**

order_items → products → category translation

---

## 4. Average Delivery Time

**Definition:** Average number of days between the order purchase timestamp and the actual customer delivery date.

**Tables used:**
- `olist_orders_dataset`

**Important:** Orders without a delivery date are excluded.

**Current value:** 12.50 days

---

## 5. Late Delivery Rate

**Definition:** Percentage of orders with an actual delivery date that occurred after the estimated delivery date.

**Formula:**

Late delivery rate =
late delivered orders / orders with a delivered date × 100

**Tables used:**
- `olist_orders_dataset`

**Important:** Orders with a NULL delivered date are excluded.

**Current value:** 8.11%
