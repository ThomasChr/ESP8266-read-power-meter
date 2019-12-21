<?php

$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";
$sensorid = 5;

$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
   die("Error 3");
}

$kwh_since_start_before = 0;
$id_before = 0;
$numUpdated = 0;
$actrowselect = "select id, kwh_since_start, kwh_since_last_send from sensorvalues where sensorid = " . $sensorid . " order by `timestamp` asc";
$actrowresult = $conn->query($actrowselect);
if ($actrowresult->num_rows > 0) {
    while($actrow = $actrowresult->fetch_assoc()) {
        $kwh_since_last_send = round($actrow['kwh_since_start'] - $kwh_since_start_before, 5);
        if ($kwh_since_last_send < 0) {
            echo "Possible restart on ID " . $id_before . " (" . $kwh_since_start_before . ") -> " . $actrow['id'] . " (" . $actrow['kwh_since_start'] . "). Please check!\n";
            if ($kwh_since_last_send < -0.5) {
                echo "-> Setting startvalue\n";
                $kwh_since_last_send = $actrow['kwh_since_start'];
            } else {
                echo "-> Setting zero\n";
                $kwh_since_last_send = 0;
            }
        }
        if ($kwh_since_last_send != $actrow['kwh_since_last_send']) {
            $numUpdated++;
            $sql = "UPDATE sensorvalues SET kwh_since_last_send = " . $kwh_since_last_send . " WHERE id = " . $actrow['id'];
            mysqli_query($conn, $sql);
            mysqli_commit($conn);
            echo "ID: " . $actrow['id'] . " (" . $kwh_since_last_send . "). UPDATED\n";
        } else {
            echo "ID: " . $actrow['id'] . " (" . $kwh_since_last_send . ").\n";
        }
        
        $id_before = $actrow['id'];
        $kwh_since_start_before = $actrow['kwh_since_start'];
    }
}

echo "Updated rows: " . $numUpdated . "\nDone.\n";
$conn->close();
