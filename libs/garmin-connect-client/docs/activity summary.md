```py
summary = garmin.get_activity(18923007987)
    
{
    "activityId": 18923007987,
    "activityUUID": {"uuid": "d982fbc3-6efe-4963-97d2-0039934b7fec"},
    "activityName": "Verdellino - 6x300m",
    "userProfileId": 113739130,
    "isMultiSportParent": False,
    "activityTypeDTO": {
        "typeId": 1,
        "typeKey": "running",
        "parentTypeId": 17,
        "isHidden": False,
        "restricted": False,
        "trimmable": True,
    },
    "eventTypeDTO": {"typeId": 9, "typeKey": "uncategorized", "sortOrder": 10},
    "accessControlRuleDTO": {"typeId": 3, "typeKey": "subscribers"},
    "timeZoneUnitDTO": {
        "unitId": 124,
        "unitKey": "Europe/Paris",
        "factor": 0.0,
        "timeZone": "Europe/Paris",
    },
    "metadataDTO": {
        "isOriginal": True,
        "deviceApplicationInstallationId": 993117,
        "agentApplicationInstallationId": None,
        "agentString": None,
        "fileFormat": {"formatId": 7, "formatKey": "fit"},
        "associatedCourseId": None,
        "lastUpdateDate": "2025-04-24T15:56:01.0",
        "uploadedDate": "2025-04-24T15:56:00.0",
        "videoUrl": None,
        "hasPolyline": True,
        "hasChartData": True,
        "hasHrTimeInZones": True,
        "hasPowerTimeInZones": True,
        "userInfoDto": {
            "userProfilePk": 113739130,
            "displayname": "3c9af3f5-eec2-4047-b9d8-bc98d3bb88c3",
            "fullname": "Paolo",
            "profileImageUrlLarge": "https://s3.amazonaws.com/garmin-connect-prod/profile_images/54ac91f0-443c-4611-a585-eb18d69ae44e-prof.png",
            "profileImageUrlMedium": "https://s3.amazonaws.com/garmin-connect-prod/profile_images/54ac91f0-443c-4611-a585-eb18d69ae44e-prfr.png",
            "profileImageUrlSmall": "https://s3.amazonaws.com/garmin-connect-prod/profile_images/54ac91f0-443c-4611-a585-eb18d69ae44e-prth.png",
            "userPro": False,
        },
        "childIds": [],
        "childActivityTypes": [],
        "sensors": [
            {
                "manufacturer": "GARMIN",
                "serialNumber": 3511385941,
                "sku": "006-B4606-00",
                "fitProductNumber": 4606,
                "sourceType": "ANTPLUS",
                "antplusDeviceType": "HEART_RATE",
                "softwareVersion": 3.9,
                "batteryStatus": "OK",
            }
        ],
        "activityImages": [],
        "manufacturer": "GARMIN",
        "diveNumber": None,
        "lapCount": 18,
        "associatedWorkoutId": 1090297018,
        "isAtpActivity": None,
        "deviceMetaDataDTO": {
            "deviceId": "3444001964",
            "deviceTypePk": 37086,
            "deviceVersionPk": 993117,
        },
        "hasIntensityIntervals": True,
        "hasSplits": True,
        "eBikeMaxAssistModes": None,
        "eBikeBatteryUsage": None,
        "eBikeBatteryRemaining": None,
        "eBikeAssistModeInfoDTOList": None,
        "hasRunPowerWindData": True,
        "calendarEventInfo": None,
        "groupRideUUID": None,
        "hasHeatMap": False,
        "autoCalcCalories": False,
        "favorite": False,
        "gcj02": False,
        "runPowerWindDataEnabled": True,
        "personalRecord": False,
        "elevationCorrected": False,
        "manualActivity": False,
        "trimmed": False,
    },
    "summaryDTO": {
        "startTimeLocal": "2025-04-24T16:42:20.0",
        "startTimeGMT": "2025-04-24T14:42:20.0",
        "startLatitude": 45.6090556550771,
        "startLongitude": 9.61661584675312,
        "distance": 9621.27,
        "duration": 3951.354,
        "movingDuration": 3598.523,
        "elapsedDuration": 4060.752,
        "elevationGain": 38.0,
        "elevationLoss": 35.0,
        "maxElevation": 190.4,
        "minElevation": 172.2,
        "averageSpeed": 2.434999942779541,
        "averageMovingSpeed": 2.6736718216422166,
        "maxSpeed": 7.250000000000001,
        "calories": 801.0,
        "bmrCalories": 96.0,
        "averageHR": 123.0,
        "maxHR": 164.0,
        "minHR": 80.0,
        "averageRunCadence": 129.90625,
        "maxRunCadence": 220.0,
        "averageTemperature": 26.05018532916739,
        "maxTemperature": 29.0,
        "minTemperature": 24.0,
        "averagePower": 264.0,
        "maxPower": 812.0,
        "minPower": 0.0,
        "normalizedPower": 364.0,
        "totalWork": 248.9248261344815,
        "groundContactTime": 264.0,
        "strideLength": 110.3699951171875,
        "verticalOscillation": 8.20999984741211,
        "trainingEffect": 3.700000047683716,
        "anaerobicTrainingEffect": 4.400000095367432,
        "aerobicTrainingEffectMessage": "IMPROVING_AEROBIC_FITNESS_2",
        "anaerobicTrainingEffectMessage": "HIGHLY_IMPROVING_ANAEROBIC_CAPACITY_AND_POWER_3",
        "verticalRatio": 8.119999885559082,
        "endLatitude": 45.609086751937866,
        "endLongitude": 9.616676112636924,
        "maxVerticalSpeed": 0.600006103515625,
        "waterEstimated": 1014.0,
        "minRespirationRate": 22.670000076293945,
        "maxRespirationRate": 50.2599983215332,
        "avgRespirationRate": 37.65999984741211,
        "trainingEffectLabel": "ANAEROBIC_CAPACITY",
        "activityTrainingLoad": 384.4158630371094,
        "minActivityLapDuration": 48.294,
        "directWorkoutFeel": 75,
        "directWorkoutRpe": 60,
        "directWorkoutComplianceScore": 100,
        "moderateIntensityMinutes": 13,
        "vigorousIntensityMinutes": 51,
        "steps": 8946,
        "beginPotentialStamina": 99.0,
        "endPotentialStamina": 48.0,
        "minAvailableStamina": 47.0,
        "avgGradeAdjustedSpeed": 2.446000099182129,
        "differenceBodyBattery": -11,
    },
    "locationName": "Verdellino",
    "splitSummaries": [
        {
            "distance": 83.03,
            "duration": 264.609,
            "movingDuration": 0.0,
            "elevationGain": 0.0,
            "elevationLoss": 0.0,
            "averageSpeed": 0.3140000104904174,
            "maxSpeed": 0.0,
            "calories": 39.0,
            "bmrCalories": 6.0,
            "averageHR": 112.0,
            "maxHR": 158.0,
            "averageRunCadence": 25.875,
            "maxRunCadence": 105.0,
            "averageTemperature": 25.0,
            "maxTemperature": 28.0,
            "minTemperature": 24.0,
            "averagePower": 0.0,
            "maxPower": 0.0,
            "normalizedPower": 206.0,
            "strideLength": 3.3601212355205496,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.0,
            "avgGradeAdjustedSpeed": 0.0,
            "splitType": "RWD_STAND",
            "noOfSplits": 25,
            "maxElevationGain": 0.0,
            "averageElevationGain": 0.0,
            "maxDistance": 9,
            "maxDistanceWithPrecision": 9.2,
        },
        {
            "distance": 3387.57,
            "duration": 1196.473,
            "movingDuration": 1175.0,
            "elevationGain": 7.0,
            "elevationLoss": 17.0,
            "averageSpeed": 2.8310000896453857,
            "averageMovingSpeed": 2.8830383560505317,
            "maxSpeed": 5.644999980926514,
            "calories": 277.0,
            "bmrCalories": 29.0,
            "averageHR": 131.0,
            "maxHR": 157.0,
            "averageRunCadence": 157.03125,
            "maxRunCadence": 195.0,
            "averageTemperature": 26.0,
            "maxTemperature": 28.0,
            "minTemperature": 25.0,
            "averagePower": 326.0,
            "maxPower": 572.0,
            "normalizedPower": 350.0,
            "groundContactTime": 274.29998779296875,
            "strideLength": 107.80000000000001,
            "verticalOscillation": 9.130000305175782,
            "verticalRatio": 8.569999694824219,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.0,
            "avgGradeAdjustedSpeed": 2.8210000991821285,
            "splitType": "INTERVAL_COOLDOWN",
            "noOfSplits": 1,
            "maxElevationGain": 7.0,
            "averageElevationGain": 7.0,
            "maxDistance": 3387,
            "maxDistanceWithPrecision": 3387.57,
        },
        {
            "distance": 1569.08,
            "duration": 1504.545,
            "movingDuration": 1182.0,
            "elevationGain": 6.0,
            "elevationLoss": 3.0,
            "averageSpeed": 1.0429999828338623,
            "averageMovingSpeed": 1.3439704091895261,
            "maxSpeed": 6.28000020980835,
            "calories": 222.0,
            "bmrCalories": 36.0,
            "averageHR": 113.0,
            "maxHR": 164.0,
            "averageRunCadence": 74.171875,
            "maxRunCadence": 207.0,
            "averageTemperature": 26.0,
            "maxTemperature": 29.0,
            "minTemperature": 24.0,
            "averagePower": 89.0,
            "maxPower": 628.0,
            "normalizedPower": 269.0,
            "groundContactTime": 301.8999938964844,
            "strideLength": 76.92000122070313,
            "verticalOscillation": 6.220000076293946,
            "verticalRatio": 8.880000114440918,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.0020000000949949026,
            "avgGradeAdjustedSpeed": 1.0889999866485596,
            "splitType": "INTERVAL_RECOVERY",
            "noOfSplits": 5,
            "maxElevationGain": 2.0,
            "averageElevationGain": 1.0,
            "maxDistance": 334,
            "maxDistanceWithPrecision": 334.55,
        },
        {
            "distance": 2864.62,
            "duration": 945.781,
            "movingDuration": 939.0,
            "elevationGain": 21.0,
            "elevationLoss": 6.0,
            "averageSpeed": 3.029000043869019,
            "averageMovingSpeed": 3.050713649826944,
            "maxSpeed": 3.4800000190734863,
            "calories": 227.0,
            "bmrCalories": 23.0,
            "averageHR": 124.0,
            "maxHR": 133.0,
            "averageRunCadence": 165.1875,
            "maxRunCadence": 172.0,
            "averageTemperature": 26.0,
            "maxTemperature": 28.0,
            "minTemperature": 25.0,
            "averagePower": 360.0,
            "maxPower": 438.0,
            "normalizedPower": 366.0,
            "groundContactTime": 266.6000061035156,
            "strideLength": 111.5300048828125,
            "verticalOscillation": 9.180000305175781,
            "verticalRatio": 8.239999771118164,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.01600000075995922,
            "avgGradeAdjustedSpeed": 3.1019999980926514,
            "splitType": "INTERVAL_WARMUP",
            "noOfSplits": 1,
            "maxElevationGain": 21.0,
            "averageElevationGain": 21.0,
            "maxDistance": 2864,
            "maxDistanceWithPrecision": 2864.62,
        },
        {
            "distance": 8458.91,
            "duration": 2679.728,
            "movingDuration": 2653.736,
            "elevationGain": 36.0,
            "elevationLoss": 31.0,
            "averageSpeed": 3.1570000648498535,
            "averageMovingSpeed": 3.189140368321285,
            "maxSpeed": 7.250000000000001,
            "calories": 627.0,
            "bmrCalories": 65.0,
            "averageHR": 129.0,
            "maxHR": 164.0,
            "averageRunCadence": 163.546875,
            "maxRunCadence": 220.0,
            "averageTemperature": 26.0,
            "maxTemperature": 29.0,
            "minTemperature": 24.0,
            "averagePower": 361.0,
            "maxPower": 812.0,
            "normalizedPower": 400.0,
            "groundContactTime": 264.0,
            "strideLength": 114.25,
            "verticalOscillation": 8.880000305175782,
            "verticalRatio": 8.149999618530273,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.0020000000949949026,
            "avgGradeAdjustedSpeed": 3.1989998817443848,
            "splitType": "RWD_RUN",
            "noOfSplits": 14,
            "maxElevationGain": 21.0,
            "averageElevationGain": 3.0,
            "maxDistance": 3321,
            "maxDistanceWithPrecision": 3321.13,
        },
        {
            "distance": 1079.33,
            "duration": 1007.002,
            "movingDuration": 934.0,
            "elevationGain": 2.0,
            "elevationLoss": 3.0,
            "averageSpeed": 1.0720000267028809,
            "averageMovingSpeed": 1.1273255882783144,
            "maxSpeed": 2.13700008392334,
            "calories": 135.0,
            "bmrCalories": 24.0,
            "averageHR": 111.0,
            "maxHR": 160.0,
            "averageRunCadence": 78.875,
            "maxRunCadence": 167.0,
            "averageTemperature": 26.0,
            "maxTemperature": 29.0,
            "minTemperature": 24.0,
            "averagePower": 73.0,
            "maxPower": 261.0,
            "normalizedPower": 149.0,
            "groundContactTime": 309.0,
            "strideLength": 74.2,
            "verticalOscillation": 5.7,
            "verticalRatio": 7.880000114440918,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.0,
            "avgGradeAdjustedSpeed": 1.0829999446868896,
            "splitType": "RWD_WALK",
            "noOfSplits": 32,
            "maxElevationGain": 1.0,
            "averageElevationGain": 0.0,
            "maxDistance": 300,
            "maxDistanceWithPrecision": 300.09,
        },
        {
            "distance": 1800.0,
            "duration": 304.542,
            "movingDuration": 296.709,
            "elevationGain": 4.0,
            "elevationLoss": 8.0,
            "averageSpeed": 5.910999774932861,
            "averageMovingSpeed": 6.078493105720827,
            "maxSpeed": 7.250000000000001,
            "calories": 75.0,
            "bmrCalories": 8.0,
            "averageHR": 137.0,
            "maxHR": 164.0,
            "averageRunCadence": 186.9375,
            "maxRunCadence": 220.0,
            "averageTemperature": 26.0,
            "maxTemperature": 29.0,
            "minTemperature": 24.0,
            "averagePower": 575.0,
            "maxPower": 812.0,
            "normalizedPower": 541.0,
            "groundContactTime": 181.1999969482422,
            "strideLength": 179.54000244140627,
            "verticalOscillation": 7.719999694824219,
            "verticalRatio": 4.420000076293945,
            "totalExerciseReps": 0,
            "avgVerticalSpeed": 0.0,
            "avgGradeAdjustedSpeed": 5.565000057220459,
            "splitType": "INTERVAL_ACTIVE",
            "noOfSplits": 6,
            "maxElevationGain": 2.0,
            "averageElevationGain": 1.0,
            "maxDistance": 300,
            "maxDistanceWithPrecision": 300.0,
        },
    ],
}
```
