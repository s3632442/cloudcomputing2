Notes on how I achieved my queries
-------------------------------------------------------------------------------------------------------------------------------------------------- Q1 step 1
SELECT *
FROM `s3632442-a1.a1.GS Quarterly Sept 20`
WHERE Value IS NOT NULL
    AND Account = 'Imports'
ORDER BY Value
LIMIT 10;
-------------------------------------------------------------------------------------------------------------------------------------------------- Q1 step 2
SELECT *
FROM `s3632442-a1.a1.GS Quarterly Sept 20`
WHERE Value IS NOT NULL
    AND Account = 'Exports'
ORDER BY Value DESC
LIMIT 10;
-----------------------------------------------Q1 - two subqueries for import and export then added import to export and displayed required fields got the deficit (i.e. import value - export value)
WITH ImportData AS (
    SELECT
        time_ref,
        SUM(Value) AS import_value
    FROM
        `s3632442-a1-t2.a1.gs_quarterly_sept_20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Imports'
    GROUP BY
        time_ref
),
ExportData AS (
    SELECT
        time_ref,
        SUM(Value) AS export_value
    FROM
        `s3632442-a1-t2.a1.gs_quarterly_sept_20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Exports'
    GROUP BY
        time_ref
)
SELECT
    i.time_ref,
    (i.import_value + e.export_value) AS trade_value
FROM
    ImportData i
JOIN
    ExportData e
ON
    i.time_ref = e.time_ref
ORDER BY
    trade_value DESC
LIMIT
    10;

-------------------------------------------------------------deployed

WITH TimeSlots AS (
                SELECT
                SUBSTR(CAST(`time_ref` AS STRING), 1, 6) AS time_slot,
                SUM(value) AS trade_value
                FROM
                `s3632442-a1-t2.a1.gs_quarterly_sept_20`
                GROUP BY
                time_slot
            )

            SELECT
                time_slot AS year_and_month,
                trade_value AS trade_value
            FROM
                TimeSlots
            ORDER BY
                trade_value DESC
            LIMIT
                10;

--------------------------------------------------------------------------------------------------------------------- Q2 step 1
WITH ImportData AS (
    SELECT
        `Time Ref` AS time_ref,
        SUM(Value) AS import_value
    FROM
        `s3632442-a1.a1.GS Quarterly Sept 20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Imports'
    GROUP BY
        time_ref
),
ExportData AS (
    SELECT
        `Time Ref` AS time_ref,
        SUM(Value) AS export_value
    FROM
        `s3632442-a1.a1.GS Quarterly Sept 20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Exports'
    GROUP BY
        time_ref
)
SELECT
    i.time_ref,
    (i.import_value - e.export_value) AS trade_deficit
FROM
    ImportData i
JOIN
    ExportData e
ON
    i.time_ref = e.time_ref
ORDER BY
    trade_deficit DESC
LIMIT
    40;
--------------------------- Q2 - two subqueries for export and import data then did sum for trade deficit (i.e. import value - export value) then displayed extra fields extended limit and ordered in DESC
WITH ImportData AS (
    SELECT
        `Time Ref` AS time_ref,
        `Coutnry Code` AS country_code,
        SUM(Value) AS import_value
    FROM
        `s3632442-a1.a1.GS Quarterly Sept 20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Imports'
        AND `Time Ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
    GROUP BY
        time_ref, country_code
),
ExportData AS (
    SELECT
        `Time Ref` AS time_ref,
        `Coutnry Code` AS country_code,
        SUM(Value) AS export_value
    FROM
        `s3632442-a1.a1.GS Quarterly Sept 20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Exports'
        AND `Time Ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
    GROUP BY
        time_ref, country_code
),
TradeDeficit AS (
    SELECT
        i.time_ref,
        c.`Country Label` AS country_label,
        'Imports' AS product_type,
        (i.import_value - e.export_value) AS trade_deficit_value,
        'F' AS status
    FROM
        ImportData i
    LEFT JOIN
        ExportData e
    ON
        i.time_ref = e.time_ref
        AND i.country_code = e.country_code
    LEFT JOIN
        `s3632442-a1.a1.Country Classification` AS c
    ON
        i.country_code = c.`Country Code`
    WHERE
        e.export_value IS NOT NULL
        AND c.`Country Label` <> 'Total' -- Exclude Total country labels
)
SELECT
    country_label,
    product_type,
    trade_deficit_value,
    status
FROM
    TradeDeficit
ORDER BY
    trade_deficit_value DESC
LIMIT
    25;

deployed

WITH TradeDeficit AS (
                SELECT
                c.country_label,
                g.`product_type` AS product_type,
                SUM(CASE WHEN g.`product_type` = 'Imports' THEN g.value ELSE -g.value END) AS trade_deficit_value,
                g.status AS status
                FROM
                `s3632442-a1-t2.a1.gs_quarterly_sept_20` AS g
                JOIN
                `s3632442-a1-t2.a1.country_classification` AS c
                ON
                g.`country_code` = c.`country_code`
                WHERE
                g.`time_ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
                AND g.status = 'F' -- Filter for status 'F'
                GROUP BY
                country_label, product_type, status
            )
            
            SELECT
                country_label,
                product_type,
                SUM(trade_deficit_value) AS trade_deficit_value,
                status
            FROM
                TradeDeficit
            GROUP BY
                country_label, product_type, status
            ORDER BY
                trade_deficit_value DESC
            LIMIT
                40;

----------------------------------------------------------------------------------------------------------------------------------------------Q3 step 1
WITH ImportData AS (
    SELECT
        `Time Ref` AS time_ref,
        `Coutnry Code` AS country_code,
        `Code` AS service_code,
        SUM(Value) AS import_value
    FROM
        `s3632442-a1.a1.GS Quarterly Sept 20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Imports'
        AND `Time Ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
        AND `Product Type`= 'Services'
    GROUP BY
        time_ref, country_code, service_code
),
ExportData AS (
    SELECT
        `Time Ref` AS time_ref,
        `Coutnry Code` AS country_code,
        `Product Type` AS product_type,
        `Code` AS service_code,
        SUM(Value) AS export_value
    FROM
        `s3632442-a1.a1.GS Quarterly Sept 20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Exports'
        AND `Time Ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
        AND `Product Type` = 'Services'
    GROUP BY
        time_ref, country_code, product_type, service_code
),
TradeSurplus AS (
    SELECT
        i.time_ref,
        c.`Country Label` AS country_label,
        'Services' AS product_type,
        i.service_code,
        (i.import_value - e.export_value) AS trade_surplus_value,
        'F' AS status
    FROM
        ImportData i
    LEFT JOIN
        ExportData e
    ON
        i.time_ref = e.time_ref
        AND i.country_code = e.country_code
    LEFT JOIN
        `s3632442-a1.a1.Country Classification` AS c
    ON
        i.country_code = c.`Country Code`
    WHERE
        e.export_value IS NOT NULL
        AND c.`Country Label` <> 'Total' -- Exclude Total country labels
)
SELECT
    country_label,
    product_type,
    service_code,
    trade_surplus_value,
    status
FROM
    TradeSurplus
ORDER BY
    trade_surplus_value DESC
LIMIT
    25;
--------------------------------Q3 brought in the service code field, changed the evaluation for trade surplus (i.e. export value - import value) and joined in the service classification on service code
WITH ImportData AS (
    SELECT
        time_ref,
        country_code,
        service_code,
        SUM(Value) AS import_value
    FROM
        `s3632442-a1-t2.a1.gs_quarterly_sept_20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Imports'
        AND time_ref BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
        AND product_type = 'Services'
    GROUP BY
        time_ref, country_code, service_code
),
ExportData AS (
    SELECT
        time_ref AS time_ref,
         country_code,
        product_type AS product_type,
        service_code,
        SUM(Value) AS export_value
    FROM
        `s3632442-a1-t2.a1.gs_quarterly_sept_20`
    WHERE
        Value IS NOT NULL
        AND Account = 'Exports'
        AND time_ref BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
        AND product_type = 'Services'
    GROUP BY
        time_ref, country_code, product_type, service_code
),
TradeSurplus AS (
    SELECT
        i.time_ref,
        c.country_label AS country_label,
        'Services' AS product_type,
        i.service_code,
        (e.export_value - i.import_value) AS trade_surplus_value,
        'F' AS status
    FROM
        ImportData i
    LEFT JOIN
        ExportData e
    ON
        i.time_ref = e.time_ref
        AND i.country_code = e.country_code
    LEFT JOIN
        `s3632442-a1-t2.a1.country_classification` AS c
    ON
        i.country_code = c.country_code
    WHERE
        e.export_value IS NOT NULL
        AND c.country_label <> 'Total' -- Exclude Total country labels
)
SELECT
    ts.service_code,
    sc.`Service Label` AS service_label,
    trade_surplus_value
FROM
    TradeSurplus ts
JOIN
    `s3632442-a1.a1.Services Classification` AS sc
ON
    ts.service_code = sc.`Code`
ORDER BY
    trade_surplus_value DESC
LIMIT
    25;

deployed

WITH ImportData AS (
    SELECT
        `time_ref` AS time_ref,
        `country_code` AS country_code,
        `service_code` AS service_code,
        SUM(value) AS import_value
            FROM
                `s3632442-a1-t2.a1.gs_quarterly_sept_20`
            WHERE
                value IS NOT NULL
                AND account = 'Imports'
                AND `time_ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
                AND `product_type`= 'Services'
            GROUP BY
                time_ref, country_code, service_code
        ),
        ExportData AS (
            SELECT
                `time_ref` AS time_ref,
                `country_code` AS country_code,
                `product_type` AS product_type,
                `service_code` AS service_code,
                SUM(value) AS export_value
            FROM
                `s3632442-a1-t2.a1.gs_quarterly_sept_20`
            WHERE
                value IS NOT NULL
                AND account = 'Exports'
                AND `time_ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
                AND `product_type` = 'Services'
            GROUP BY
                time_ref, country_code, product_type, service_code
        ),
        TradeSurplus AS (
            SELECT
                i.time_ref,
                c.country_label AS country_label,
                'Services' AS product_type,
                i.service_code,
                (e.export_value - i.import_value) AS trade_surplus_value,
                'F' AS status
            FROM
                ImportData i
            LEFT JOIN
                ExportData e
            ON
                i.time_ref = e.time_ref
                AND i.country_code = e.country_code
            LEFT JOIN
                `s3632442-a1-t2.a1.country_classification` AS c
            ON
                i.country_code = c.`country_code`
            WHERE
                e.export_value IS NOT NULL
                AND c.country_label <> 'Total' -- Exclude Total country labels
        )
        SELECT
            sc.`service_label` AS service_label,
            trade_surplus_value
        FROM
            TradeSurplus ts
        JOIN
            `s3632442-a1-t2.a1.service_classification` AS sc
        ON
            ts.service_code = sc.`service_code`
        ORDER BY
            trade_surplus_value DESC
        LIMIT
            25;