<?php
session_start();
require __DIR__ . '/vendor/autoload.php';
?>

<!DOCTYPE html>
<html>
<head>
    <title>A1 - Task 2</title>
    <meta charset='UTF-8'>
    <link href='https://fonts.googleapis.com/css?family=Cabin' rel='stylesheet' type='text/css'>
    <link rel='stylesheet' type='text/css' href='/css/style.css'>
    <style>
    /* Define the styles for the tabs and tab content */
    .tab-container {
        display: flex;
        flex-direction: column; /* Change to column to stack tabs vertically */
        align-items: center;
    }

    .table-container {
        text-align: center;
    }

    .tab {
        display: none;
    }

    .tab-link {
        cursor: pointer;
        padding: 10px;
        background-color: #212121;
        border: 1px solid #1f7cff;
        border-radius: 5px;
        margin-bottom: 5px; /* Change margin to separate tabs vertically */
    }

    .tab-link.active {
        background-color: #1f7cff;
    }

    /* Style the table */
    table {
        border-collapse: collapse;
        width: 80%;
        margin: 0 auto;
    }

    th, td {
        border: 1px solid #ccc;
        padding: 8px;
        text-align: left;
    }

    th {
        background-color: #eee;
    }
	</style>

    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        $(document).ready(function(){
            // Show the default tab on page load
            $(".tab-link[data-tab-id='tab1']").addClass("active"); // Highlight the default tab

            // Function to switch tabs and show corresponding content
            $(".tab-link").click(function() {
                var tabId = $(this).attr("data-tab-id");
                $(".tab").css("display", "none"); // Hide all tabs
                $("#" + tabId).css("display", "block"); // Show the selected tab

                // Remove the "active" class from all tab links
                $(".tab-link").removeClass("active");
                // Add the "active" class to the clicked tab link
                $(this).addClass("active");
            });
        });
    </script>
</head>
<body>
<div id='header'>
    A1 - TASK 2
</div>
<div class='content'>
    <div class="tab-container">
        <!-- Tab links -->
        <div class="tab-link" data-tab-id="tab1">Show top 10 time slots with the highest trade value</div>
        <div class="tab-link" data-tab-id="tab2">25 services with the highest total trade surplus value</div>
        <div class="tab-link" data-tab-id="tab3">Show top 25 services with the highest total trade surplus value</div>
    </div>
    
	<div class="table-container"> <!-- Added a container for the table -->
		<!-- Tab content -->
		<div id="tab1" class="tab">
		<?php
			// Your PHP code for Tab 1 results
			use Google\Cloud\BigQuery\BigQueryClient;

			$projectId = 's3632442-a1';
			$client = new BigQueryClient([
				'projectId' => $projectId,
			]);
			$query = "WITH TimeSlots AS (
				SELECT
				SUBSTR(CAST(`Time Ref` AS STRING), 1, 6) AS time_slot,
				SUM(Value) AS trade_value
				FROM
				`s3632442-a1.a1.GS Quarterly Sept 20`
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
				10;";
			$queryJobConfig = $client->query($query);
			$queryResults = $client->runQuery($queryJobConfig);

			$str = "<table>".
			"<tr>" .
			"<th>Year and Month</th>" .
			"<th>Trade Value</th>" .
			"</tr>";

			if ($queryResults->isComplete()) {
				$rows = $queryResults->rows();

				foreach ($rows as $row)
				{
					$str .= "<tr>";

					foreach ($row as $field)
					{
						$str .= "<td>" . $field . "</td>";
					}
					$str .= "</tr>";
				}
			} else {
				throw new Exception('The query failed to complete');
			}

			$str .= '</table>';

			echo $str;
			?>

		</div>
		<div id="tab2" class="tab">
		<?php
			// Your PHP code for Tab 2 results
			

			$projectId = 's3632442-a1';
			$client = new BigQueryClient([
				'projectId' => $projectId,
			]);
			$query = "WITH TradeDeficit AS (
				SELECT
				c.`Country Label` AS country_label,
				g.`Product Type` AS product_type,
				SUM(CASE WHEN g.`Product Type` = 'Imports' THEN g.Value ELSE -g.Value END) AS trade_deficit_value,
				g.Status AS status
				FROM
				`s3632442-a1.a1.GS Quarterly Sept 20` AS g
				JOIN
				`s3632442-a1.a1.Country Classification` AS c
				ON
				g.`Coutnry Code` = c.`Country Code`
				WHERE
				g.`Time Ref` BETWEEN 201301 AND 201512 -- Filter for 2013 to 2015
				AND g.Status = 'F' -- Filter for status 'F'
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
				40;";
			$queryJobConfig = $client->query($query);
			$queryResults = $client->runQuery($queryJobConfig);

			$str = "<table>".
			"<tr>" .
			"<th>Country Label</th>" .
			"<th>Product Type</th>" .
			"<th>Trade Deficit Value</th>" .
			"<th>Status</th>" .
			"</tr>";

			if ($queryResults->isComplete()) {
				$rows = $queryResults->rows();

				foreach ($rows as $row)
				{
					$str .= "<tr>";

					foreach ($row as $field)
					{
						$str .= "<td>" . $field . "</td>";
					}
					$str .= "</tr>";
				}
			} else {
				throw new Exception('The query failed to complete');
			}

			$str .= '</table>';

			echo $str;
			?>
		</div>
		<div id="tab3" class="tab">
		<?php
			// Your PHP code for Tab 3 results
			$projectId = 's3632442-a1';
			$client = new BigQueryClient([
				'projectId' => $projectId,
			]);
			$query = "WITH TopTimeSlots AS (
				-- Retrieve the top 10 time slots from GS Quarterly Sept 20
				SELECT
					`Time Ref` AS time_ref
				FROM
					`s3632442-a1.a1.GS Quarterly Sept 20`
				GROUP BY
					`Time Ref`
				ORDER BY
					SUM(CASE WHEN Status = 'F' THEN Value ELSE 0 END) DESC
				LIMIT
					10
			),
			
			TopCountries AS (
				-- Retrieve the top 40 countries from Country Classification
				SELECT
					`Country Code` AS Country_Code
				FROM
					`s3632442-a1.a1.Country Classification`
				LIMIT
					40
			)
			
			-- Join the results with the Services Classification table to get service names
			SELECT
				sc.`Service Label` AS service_label,
				SUM(CASE WHEN gsq.`Product Type` = 'Exports' THEN gsq.Value ELSE 0 END) -
				SUM(CASE WHEN gsq.`Product Type` = 'Imports' THEN gsq.Value ELSE 0 END) AS trade_surplus_value
			FROM
				`s3632442-a1.a1.GS Quarterly Sept 20` AS gsq
			JOIN
				`s3632442-a1.a1.Services Classification` AS sc
			ON
				gsq.Code = sc.Code
			JOIN
				TopTimeSlots AS tts
			ON
				gsq.`Time Ref` = tts.time_ref
			JOIN
				TopCountries AS tc
			ON
				gsq.`Coutnry Code` = tc.Country_Code
			GROUP BY
				sc.`Service Label`
			ORDER BY
				trade_surplus_value DESC
			LIMIT
				25;";
			$queryJobConfig = $client->query($query);
			$queryResults = $client->runQuery($queryJobConfig);

			$str = "<table>".
			"<tr>" .
			"<th>Service Label</th>" .
			"<th>Trade Surplus Value</th>" .
			"</tr>";

			if ($queryResults->isComplete()) {
				$rows = $queryResults->rows();

				foreach ($rows as $row)
				{
					$str .= "<tr>";

					foreach ($row as $field)
					{
						$str .= "<td>" . $field . "</td>";
					}
					$str .= "</tr>";
				}
			} else {
				throw new Exception('The query failed to complete');
			}

			$str .= '</table>';

			echo $str;
			?>
		</div>
	</div>
</div>
</body>
</html>



