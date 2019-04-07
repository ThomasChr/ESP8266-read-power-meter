<php

/* globals */
$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";
$fetchdays = 30;
$cent_per_kwh = 27.88;
$sensorid = 5;
$mailrecp;

/* connect db */
$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
    die("DB connect failed");
}

/* power yesterday */
$yesterdayresult = $conn->query("select sum(kwh_since_last_send) from envsensors where sensorid = " . $sensorid . " and date(timestamp) = (curdate() - 1)");
$yesterdayrow = $yesterdayresult->fetch_assoc();
$yesterdaykwh = $yesterdayrow[0];

/* power this week */

/* power this month */

/* power this year */

/* consumption for the last $fetchdays days */

/* build the mailtext */
$mailtext = "Verbrauch gestern: " . $yesterdaykwh . " kwh (" . ($yesterdaykwh * $cent_per_kwh / 100) . " EUR)\n";

/* send mail */
mail($mailrecp, "Stromdaten", $mailtext);

echo "Done.";

$conn->close();

?>