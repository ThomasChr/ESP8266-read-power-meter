<?php

$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";

$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);

$sensorselect = "select id, name from sensors where monitoring = 1 order by id asc";
$sensorresult = $conn->query($sensorselect);
if ($sensorresult->num_rows > 0) {
    while($sensorrow = $sensorresult->fetch_assoc()) {
        echo "Prüfe Sensor " . $sensorrow['id'] . "<br>";

        $checkselect = "select id from sensorvalues where sensorid = " . $sensorrow['id'] . " and timestamp >= date_sub(now(), interval 15 minute)";
        $checkresult = $conn->query($checkselect);
        
        if ($checkresult->num_rows == 0) {
            echo "Keine Daten. Sende Mail!<br>";
            mail("me@myserver.de", "Temperatursensor " . $sensorrow['id'] . " (" . $sensorrow['name'] . ") hat in den letzten 15 Minuten keine Daten gemeldet!", "no text");
        } 
    }
}

echo "Done.";

$conn->close();

?>
