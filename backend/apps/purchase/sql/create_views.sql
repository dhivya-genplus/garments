-- ============================================================================
-- Yarn Purchase Order (Yarn PO) Tracking & Balance Views
-- ============================================================================

-- 1. yarn_po_balance: Tracks ordered vs inward received balances
CREATE OR REPLACE VIEW yarn_po_balance AS
SELECT 
    po.id AS po_id,
    po.po_number,
    po.yarn_type,
    po.yarn_count_id,
    po.party_id,
    po.bag AS ord_bags,
    po.quantity AS po_quantity,
    COALESCE(SUM(child.bag - child.remaining_bag), 0) AS in_bag,
    COALESCE(SUM(child.quantity - child.remaining_quantity), 0) AS in_quantity,
    (po.quantity - COALESCE(SUM(child.quantity - child.remaining_quantity), 0)) AS balance_quantity
FROM tm_yarn_po po
LEFT JOIN tx_purchase_order child ON child.tm_po_id = po.id AND child.status = 1
WHERE po.status = 1
GROUP BY po.id, po.po_number, po.yarn_type, po.yarn_count_id, po.party_id, po.bag, po.quantity;


-- 2. yarn_po_sum: Aggregates ordered vs received bags and weights per PO and Yarn Count
CREATE OR REPLACE VIEW yarn_po_sum AS
SELECT 
    po.id AS tm_po_id,
    child.yarn_count_id,
    child.yarn_type,
    SUM(child.bag) AS total_ordered_bags,
    SUM(child.quantity) AS total_ordered_quantity,
    SUM(child.bag - child.remaining_bag) AS total_received_bags,
    SUM(child.quantity - child.remaining_quantity) AS total_received_quantity
FROM tm_yarn_po po
JOIN tx_purchase_order child ON child.tm_po_id = po.id
WHERE po.status = 1 AND child.status = 1
GROUP BY po.id, child.yarn_count_id, child.yarn_type;


-- 3. y_po_sum: Summary of scheduled deliveries per destination party
CREATE OR REPLACE VIEW y_po_sum AS
SELECT 
    d.tm_po_id,
    d.party_id,
    p.name AS destination_name,
    SUM(d.bag) AS total_delivery_bags,
    SUM(d.quantity) AS total_delivery_quantity
FROM tx_yarn_po d
JOIN mx_party p ON p.id = d.party_id
WHERE d.status = 1
GROUP BY d.tm_po_id, d.party_id, p.name;
