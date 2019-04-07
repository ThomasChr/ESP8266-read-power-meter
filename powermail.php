<?php

/* globals */
$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";
$fetchdays = 30;
$cent_per_kwh = 27.88;
$sensorid = 5;
$mailrecp = "none@nowhere.com";
$starttime = mktime(0, 0, 0, date("m", time()), date("d", time()), date("Y", time()));

/* connect db */
$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
    die("DB connect failed");
}

/* power yesterday */
$yesterdayresult = $conn->query("select sum(kwh_since_last_send) as sum from sensorvalues where sensorid = " . $sensorid . " and date(timestamp) = (curdate() - 1);");
$yesterdayrow = $yesterdayresult->fetch_assoc();
$yesterdaykwh = $yesterdayrow["sum"];

/* power this week */
$thisweekresult = $conn->query("select sum(kwh_since_last_send) as sum from sensorvalues where sensorid = " . $sensorid . " and week(timestamp, 1) = week(curdate(), 1) and year(timestamp) = year(curdate());");
$thisweekrow = $thisweekresult->fetch_assoc();
$thisweekkwh = $thisweekrow["sum"];

/* power this month */
$thismonthresult = $conn->query("select sum(kwh_since_last_send) as sum from sensorvalues where sensorid = " . $sensorid . " and month(timestamp) = month(curdate()) and year(timestamp) = year(curdate());");
$thismonthrow = $thismonthresult->fetch_assoc();
$thismonthkwh = $thismonthrow["sum"];

/* power this year */
$thisyearresult = $conn->query("select sum(kwh_since_last_send) as sum from sensorvalues where sensorid = " . $sensorid . " and year(timestamp) = year(curdate());");
$thisyearrow = $thisyearresult->fetch_assoc();
$thisyearkwh = $thisyearrow["sum"];

/* consumption for the last $fetchdays days */
$dayconsumption = "";
$daysresult = $conn->query("select sum(kwh_since_last_send) as sum, date(timestamp) as day, dayname(timestamp) as dayname from sensorvalues where sensorid = " . $sensorid . " group by date(timestamp) order by timestamp DESC LIMIT 0, " . $fetchdays . ";");
while($daysrow = $daysresult->fetch_assoc()) {
    $dayconsumption .= $daysrow["dayname"] . ", " . $daysrow["day"] . ": " . round($daysrow["sum"], 2) . " kwh (" . round(($daysrow["sum"] * $cent_per_kwh / 100), 2) . " EUR)\n";
}

/* build the mailtext */
$mailtext = "Es ist der " . date("d.m.Y", $starttime) . ":\n";
$mailtext .= "Verbrauch gestern: " . round($yesterdaykwh, 2) . " kwh (" . round(($yesterdaykwh * $cent_per_kwh / 100), 2) . " EUR)\n";
$mailtext .= "Verbrauch diese Woche: " . round($thisweekkwh, 2) . " kwh (" . round(($thisweekkwh * $cent_per_kwh / 100), 2) . " EUR)\n";
$mailtext .= "Verbrauch dieses Monat: " . round($thismonthkwh, 2) . " kwh (" . round(($thismonthkwh * $cent_per_kwh / 100), 2) . " EUR)\n";
$mailtext .= "Verbrauch dieses Jahr: " . round($thisyearkwh, 2) . " kwh (" . round(($thisyearkwh * $cent_per_kwh / 100), 2) . " EUR)\n\n";
$mailtext .= $dayconsumption;

/* send mail */
mail($mailrecp, "Stromdaten", $mailtext);
echo $mailtext;

$conn->close();

?>