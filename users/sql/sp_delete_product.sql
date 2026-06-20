CREATE OR REPLACE PROCEDURE sp_delete_product(IN p_product_id BIGINT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Delete settlements for orders of this product
    DELETE FROM order_settlements
    WHERE order_id IN (
        SELECT id
        FROM orders
        WHERE product_id = p_product_id
    );

    -- Delete orders
    DELETE FROM orders
    WHERE product_id = p_product_id;

    -- Delete variants
    DELETE FROM product_variants
    WHERE product_id = p_product_id;

    -- Delete product
    DELETE FROM products
    WHERE id = p_product_id;

    -- Delete marketplace orders with no remaining orders
    DELETE FROM marketplace_orders mo
    WHERE NOT EXISTS (
        SELECT 1
        FROM orders o
        WHERE o.marketplace_order_id = mo.id
    );

    -- Delete customers with no remaining marketplace orders
    DELETE FROM customers c
    WHERE NOT EXISTS (
        SELECT 1
        FROM marketplace_orders mo
        WHERE mo.customer_id = c.id
    );
END;
$$;