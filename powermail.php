<php

/* globals */
$dbserver = "localhost";
$dbuser = "envsensors";
$dbpass = "4";
$dbname = "envsensors";
$fetchdays = 30;

/* connect db */
$conn = new mysqli($dbserver, $dbuser, $dbpass, $dbname);
if ($conn->connect_error) {
    die("DB connect failed");
}

/* power yesterday */

/* power this week */

/* power this month */

/* power this year */

/* consumption for the last $fetchdays days */

/* send mail */


echo "Done.";

$stmt->close();
$conn->close();

?>