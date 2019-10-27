<?php

$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";

$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
   die("Error 3");
}

$kwh_since_startbefore = 0;
$id_before = 0;
$numUpdated = 0;
$actrowselect = "select id, kwh_since_start, kwh_since_last_send from sensorvalues where sensorid = 5 order by id asc";
$actrowresult = $conn->query($actrowselect);
if ($actrowresult->num_rows > 0) {
    while($actrow = $actrowresult->fetch_assoc()) {
        $kwh_since_last_send = round($actrow['kwh_since_start'] - $kwh_since_startbefore, 5);
        if ($kwh_since_last_send < 0) {
            echo "Possible restart on ID " . $id_before . " -> " . $actrow['id'] . ". Please check!\n";
            $kwh_since_last_send = $actrow['kwh_since_start'];
        }
        echo "ID: " . $actrow['id'] . "(" . $kwh_since_last_send . ")\n";

        if ($kwh_since_last_send != $actrow['kwh_since_last_send']) {
            $numUpdated++;
            $sql = "UPDATE sensorvalues SET kwh_since_last_send = " . $kwh_since_last_send . " WHERE id = " . $actrow['id'];
            mysqli_query($conn, $sql);
            mysqli_commit($conn);
        }
        
        $id_before = $actrow['id'];
        $kwh_since_startbefore = $actrow['kwh_since_start'];
    }
}

echo "Updated rows: " . $numUpdated . "\nDone.\n";
$conn->close();
