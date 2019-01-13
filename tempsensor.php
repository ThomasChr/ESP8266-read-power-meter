<?php

$sensorpass = "3";
$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";

$sensorid = $_POST["sensorid"];
if (!isset($sensorid) || !is_numeric($sensorid)) {
    die('Error 1');
}

$password = $_POST["password"];
if (!isset($password) || !($password == $sensorpass)) {
    die('Error 2');
}

$temp = $_POST["temp"];
if (!isset($temp) || !is_numeric($temp)) {
    $temp = 0;
}

$press = $_POST["press"];
if (!isset($press) || !is_numeric($press)) {
    $press = 0;
}

$hum = $_POST["hum"];
if (!isset($hum) || !is_numeric($hum)) {
    $hum = 0;
}

$power = $_POST["power"];
if (!isset($power) || !is_numeric($power)) {
    $power = 0;
}

$kwh_since_start = $_POST["kwh_since_start"];
if (!isset($kwh_since_start) || !is_numeric($kwh_since_start)) {
    $kwh_since_start = 0;
}

$exceptiondata = $_POST["exceptiondata"];
if (!isset($exceptiondata)) {
    $exceptiondata = "";
}

$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
    die("Error 3");
}

$lastkwhselect = "select kwh_since_start from sensorvalues where sensorid = " . $sensorid . "  order by id desc limit 1";
$lastkwhresult = $conn->query($lastkwhselect);

if ($lastkwhresult->num_rows == 1) {
    $lastkwhrow = $lastkwhresult->fetch_assoc();
    $kwh_since_last_send = $kwh_since_start - $lastkwhrow['kwh_since_start'];
    if ($kwh_since_last_send < 0) {
        $kwh_since_last_send = $kwh_since_start;
    }
} else {
    $kwh_since_last_send = 0;
}

$stmt = $conn->prepare("INSERT INTO sensorvalues (sensorid, temp, press, hum, power, kwh_since_start, kwh_since_last_send, exceptiondata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
$stmt->bind_param("idddddds", $sensorid, $temp, $press, $hum, $power, $kwh_since_start, $kwh_since_last_send, $exceptiondata);
$stmt->execute();

echo "Done.";

$stmt->close();
$conn->close();

?>
