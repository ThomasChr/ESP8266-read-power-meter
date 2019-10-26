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
$actrowselect = "select id, kwh_since_start from sensorvalues where sensorid = 5 order by id asc";
$actrowresult = $conn->query($actrowselect);
if ($actrowresult->num_rows > 0) {
   while($actrow = $actrowresult->fetch_assoc()) {
       $kwh_since_last_send = round($actrow['kwh_since_start'] - $kwh_since_startbefore, 5);
       if ($kwh_since_last_send < 0) {
           $kwh_since_last_send = 0;
       }
       echo "ID: " . $actrow['id'] . "(" . $kwh_since_last_send . ")\n";

       $sql = "UPDATE sensorvalues SET kwh_since_last_send = " . $kwh_since_last_send . " WHERE id = " . $actrow['id'];
       mysqli_query($conn, $sql);
       mysqli_commit($conn);
       $kwh_since_startbefore = $actrow['kwh_since_start'];
   }
}

echo "Done.\n";
$conn->close();
