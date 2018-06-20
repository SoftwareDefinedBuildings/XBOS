<!doctype html>
<!--
	Material Design Lite
	Copyright 2015 Google Inc. All rights reserved.

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

		https://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License
-->
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
	<title>XBOS</title>
	<link rel="shortcut icon" href="images/favicon.png">
	<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:regular,bold,italic,thin,light,bolditalic,black,medium&amp;lang=en">
	<link rel="stylesheet" href="https://code.getmdl.io/1.3.0/material.amber-blue.min.css">
	<link rel="stylesheet" href="css/styles.css">
	<link rel="stylesheet" href="css/mystyle.css">
	<link rel="stylesheet" href="css/weather.css">
	<link rel="stylesheet" href="fonts/artill_clean_icons.otf">
	<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
</head>

<body>
	<div class="demo-layout mdl-layout mdl-js-layout">
		<header class="demo-header mdl-layout__header">
			<div class="mdl-layout__header-row">
				<span class="mdl-layout-title">XBOS-DR</span>
				<div class="mdl-layout-spacer"></div>
				<nav class="demo-navigation mdl-navigation">
					<a class="mdl-navigation__link navigation-active" href="index.html">Home</a>
					<a class="mdl-navigation__link" href="">Schedule</a>
					<a class="mdl-navigation__link" href="">Alert</a>
					<a class="mdl-navigation__link" href="">Report</a>
					<a class="mdl-navigation__link" href="demandResponse.html">Demand Response</a>
					<a class="mdl-navigation__link" href="">Configuration</a>
					<a class="mdl-navigation__link" href="">Users</a>
				</nav>
				<div id="weather">weather</div>
			</div>
		</header>
 
		<main class="mdl-layout__content mdl-color--grey-100">
			<div class="mdl-grid demo-content">
				<div class="demo-graphs mdl-shadow--4dp mdl-color--white mdl-cell mdl-cell--6-col">
					<div id="chart-total-energy" style="width:100%; height:300px;"></div>
					<div id="energyButtons">
						<a id="goToAll" class="waves-effect waves-light btn">All</a>
						<a id="energyChartReset" class="waves-effect waves-light btn">Reset Zoom</a>
						<a id="goToToday" class="waves-effect waves-light btn">Today</a>
					</div>
				</div>
				<div class="demo-graphs mdl-shadow--4dp mdl-color--white mdl-cell mdl-cell--6-col">
					<div id="chart-temperature" style="width:100%; height:300px;"></div>
					<div id="tempButtons">
						<a id="tempChartReset" class="waves-effect waves-light btn">Reset Zoom</a>
					</div>
				</div>
				
				<div class="demo-cards mdl-cell mdl-cell--2-col mdl-grid mdl-grid--no-spacing">
					<div class="mdl-card mdl-shadow--4dp mdl-cell mdl-cell--4-col mdl-cell--4-col-tablet mdl-cell--12-col-desktop">
						<div class="mdl-card__title mdl-color--red-600">
							<h2 class="mdl-card__title-text">Heating</h2>
						</div>
						<div class="mdl-card__supporting-text" id="heatingDiv">
						</div>
					</div>
					
					<div class="demo-separator mdl-cell--1-col"></div>

					<div class="mdl-card mdl-shadow--4dp mdl-cell mdl-cell--4-col mdl-cell--4-col-tablet mdl-cell--12-col-desktop">
						<div class="mdl-card__title mdl-color--blue-700">
							<h2 class="mdl-card__title-text">Cooling</h2>
						</div>
						<div class="mdl-card__supporting-text" id="coolingDiv">
						</div>
					</div>
					
					<div class="demo-separator mdl-cell--1-col"></div>

					<!-- <div class="mdl-card mdl-shadow--4dp"> -->
<!-- 						<div class="mdl-card__title mdl-color--yellow-700">
							<h2 class="mdl-card__title-text">Lighting</h2>
						</div>
						<div class="mdl-card__supporting-text" id="lightingDiv">
						</div> -->
					<!-- </div> -->
					
					<!-- <div class="demo-separator mdl-cell--1-col"></div> -->

					<div class="mdl-card mdl-shadow--4dp mdl-cell mdl-cell--4-col mdl-cell--4-col-tablet mdl-cell--12-col-desktop">
						<div class="mdl-card__title mdl-color--grey-900">
							<h2 class="mdl-card__title-text">Off</h2>
						</div>
						<div class="mdl-card__supporting-text" id="offDiv">
						</div>
					</div>
				</div>

				<div class="demo-charts mdl-color--white mdl-shadow--4dp mdl-cell mdl-cell--10-col mdl-grid">
					<?php require 'floorplan.php';?>
				</div>
			</div>
		</main>
	</div>

	<script src="https://code.getmdl.io/1.3.0/material.min.js"></script>
	<script src="js/lib/highcharts.js"></script>
	<script src="js/lib/highcharts-more.js"></script>
	<script src="js/lib/data.js"></script>
	<script src="js/lib/drilldown.js"></script>
	<script src="js/lib/jquery.min.js"></script>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.simpleWeather/3.1.0/jquery.simpleWeather.min.js"></script>
	<script type="text/javascript" src="js/lib/weather.js"></script>
	<script type="text/javascript" src="js/totalEnergy.js"></script>
	<script type="text/javascript" src="js/temperature.js"></script>
	<script type="text/javascript" src="js/floorplan.js"></script>

</body>
</html>
