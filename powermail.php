<?php

/* globals */
$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";
$fetchdays = 30;
$fetchmonths = 48;
$CENT_PER_KWH = 45.04;
$EURO_PER_MONTH = 12.97;
$EURO_PER_MONTH_PREPAYMENT = 90;
$sensorid = 5;
$mailrecp = "none@nowhere.com";
$starttime = mktime(0, 0, 0, date("m", time()), date("d", time()), date("Y", time()));

/* connect db */
$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
    die("DB connect failed");
}

/* power yesterday */
$yesterdayresult = $conn->query("select sum(kwh_since_last_send) as sum from sensorvalues where sensorid = " . $sensorid . " and date(timestamp) = (subdate(curdate(), 1));");
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

/* consumption for yesterdays hours */
$yesterdayhourconsumption = "";
$yesterdayhoursresult = $conn->query("select hour(timestamp) as hour, sum(kwh_since_last_send) as sum from sensorvalues where sensorid = " . $sensorid . " and date(timestamp) = (subdate(curdate(), 1)) group by hour(timestamp) order by timestamp ASC;");
while($yesterdayhoursrow = $yesterdayhoursresult->fetch_assoc()) {
    $yesterdayhourconsumption .= $yesterdayhoursrow["hour"] . " - " . ($yesterdayhoursrow["hour"] + 1) . " Uhr: " . round($yesterdayhoursrow["sum"], 2) . " kWh (" . round(($yesterdayhoursrow["sum"] * $CENT_PER_KWH / 100), 2) . " EUR)\n";
}

/* consumption for the last $fetchdays days */
$dayconsumption = "";
$daysresult = $conn->query("select sum(kwh_since_last_send) as sum, date(timestamp) as day, dayname(timestamp) as dayname from sensorvalues where sensorid = " . $sensorid . " group by date(timestamp) order by timestamp DESC LIMIT 0, " . $fetchdays . ";");
while($daysrow = $daysresult->fetch_assoc()) {
    $dayconsumption .= $daysrow["dayname"] . ", " . $daysrow["day"] . ": " . round($daysrow["sum"], 2) . " kWh (" . round(($daysrow["sum"] * $CENT_PER_KWH / 100), 2) . " EUR)\n";
}

/* consumption for the last $fetchmonths months */
$monthconsumption = "";
$monthsresult = $conn->query("select sum(kwh_since_last_send) as sum, DATE_FORMAT(timestamp,'%c/%y') as month from sensorvalues where sensorid = " . $sensorid . " group by 2 order by timestamp DESC LIMIT 0, " . $fetchmonths . ";");
while($monthsrow = $monthsresult->fetch_assoc()) {
    $monthconsumption .= $monthsrow["month"] . ": " . round($monthsrow["sum"], 2) . " kWh (" . round(($monthsrow["sum"] * $CENT_PER_KWH / 100 + $EURO_PER_MONTH), 2) . " EUR - " . round($EURO_PER_MONTH_PREPAYMENT, 2) . " EUR = " . round(($monthsrow["sum"] * $CENT_PER_KWH / 100 + $EURO_PER_MONTH) - ($EURO_PER_MONTH_PREPAYMENT), 2) . " EUR)\n";
}

/* build the mailtext */
$mailtext = "Es ist der " . date("d.m.Y", $starttime) . ":\n";
$mailtext .= "Verbrauch gestern: " . round($yesterdaykwh, 2) . " kWh (" . round(($yesterdaykwh * $CENT_PER_KWH / 100), 2) . " EUR)\n";
$mailtext .= "Verbrauch diese Woche: " . round($thisweekkwh, 2) . " kWh (" . round(($thisweekkwh * $CENT_PER_KWH / 100), 2) . " EUR)\n";
$mailtext .= "Verbrauch dieses Monat: " . round($thismonthkwh, 2) . " kWh (" . round(($thismonthkwh * $CENT_PER_KWH / 100 + $EURO_PER_MONTH), 2) . " EUR)\n";
$mailtext .= "Verbrauch dieses Jahr: " . round($thisyearkwh, 2) . " kWh (" . round(($thisyearkwh * $CENT_PER_KWH / 100 + ($EURO_PER_MONTH * date('m'))), 2) . " EUR - " . round($EURO_PER_MONTH_PREPAYMENT * date('m'), 2) . " EUR = " . round(($thisyearkwh * $CENT_PER_KWH / 100 + ($EURO_PER_MONTH * date('m'))) - ($EURO_PER_MONTH_PREPAYMENT * date('m')), 2) . " EUR)\n\n";
$mailtext .= "Preis pro kWh: " . $CENT_PER_KWH . " Cent\n";
$mailtext .= "Grundgebuehr pro Monat: " . $EURO_PER_MONTH . " Euro\n";
$mailtext .= "Abschlag pro Monat: " . $EURO_PER_MONTH_PREPAYMENT . " Euro\n\n";
$mailtext .= "Verbrauch gestern:\n";
$mailtext .= $yesterdayhourconsumption . "\n\n";
$mailtext .= "Verbrauch letzte " . $fetchdays . " Tage:\n";
$mailtext .= $dayconsumption . "\n\n";
$mailtext .= "Verbrauch letzte " . $fetchmonths . " Monate:\n";
$mailtext .= $monthconsumption . "\n\n";

/* send mail */
mail($mailrecp, "Stromdaten", $mailtext);
echo $mailtext;

$conn->close();

?>