-- phpMyAdmin SQL Dump
-- version 4.5.4.1deb2ubuntu2.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Erstellungszeit: 10. Jan 2019 um 09:02
-- Server-Version: 10.1.37-MariaDB-1~xenial
-- PHP-Version: 7.0.32-0ubuntu0.16.04.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `envsensors`
--

DELIMITER $$
--
-- Funktionen
--
CREATE DEFINER=`envsensors`@`localhost` FUNCTION `get_absolutefeuchte` (`temp` DECIMAL(10,3), `hum` DECIMAL(10,3)) RETURNS DOUBLE begin
declare sdd double default 0;
declare dd double default 0;
declare td double default 0;
declare tk double default 0;
declare af double default 0;
declare v double default 0;
declare a double default 7.5;
declare b double default 237.3;

	set sdd = 6.1078 * power(10, ((a*temp)/(b+temp)));
	set dd = hum/100 * sdd;
	set v = LOG(10, dd/6.1078);
	set td = b*v/(a-v);
	set tk = temp + 273.15;
	set af = power(10, 5) * 18.016 / 8314.3 * dd/tk;
	return af;
end$$

CREATE DEFINER=`envsensors`@`localhost` FUNCTION `get_taupunkt` (`temp` DECIMAL(10,3), `hum` DECIMAL(10,3)) RETURNS DOUBLE begin
declare sdd double default 0;
declare dd double default 0;
declare td double default 0;
declare v double default 0;
declare a double default 7.5;
declare b double default 237.3;

	set sdd = 6.1078 * power(10, ((a*temp)/(b+temp)));
	set dd = hum/100 * sdd;
	set v = LOG(10, dd/6.1078);
	set td = b*v/(a-v);
	return td;
end$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `sensors`
--

CREATE TABLE `sensors` (
  `id` int(11) NOT NULL,
  `name` varchar(32) NOT NULL,
  `description` text NOT NULL,
  `monitoring` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `sensorvalues`
--

CREATE TABLE `sensorvalues` (
  `id` bigint(20) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `sensorid` int(11) NOT NULL,
  `temp` decimal(10,3) NOT NULL,
  `press` decimal(10,3) NOT NULL,
  `hum` decimal(10,3) NOT NULL,
  `power` decimal(10,3) NOT NULL,
  `kwh_since_start` decimal(15,5) NOT NULL,
  `kwh_since_last_send` decimal(10,5) NOT NULL,
  `exceptiondata` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `sensors`
--
ALTER TABLE `sensors`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `sensorvalues`
--
ALTER TABLE `sensorvalues`
  ADD PRIMARY KEY (`id`),
  ADD KEY `timestampindex` (`timestamp`),
  ADD KEY `sensorindex` (`sensorid`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `sensors`
--
ALTER TABLE `sensors`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;
--
-- AUTO_INCREMENT für Tabelle `sensorvalues`
--
ALTER TABLE `sensorvalues`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=310166;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

