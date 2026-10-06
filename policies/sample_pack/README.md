# Sample pack

`policy_library.sample.json` is the library the prototype used to ship with: three services (lumbar spinal fusion, ICD for heart failure, bariatric surgery), their policies, rules and key facts.

The app now ships with an empty library. Nothing is built in. The policy owner adds every service.

To bring the sample services back on a machine, stop the app and copy this file over the live library:

    copy policies\sample_pack\policy_library.sample.json app\policy_library.live.json

Then start the app again. (On Render, the live file is on the data disk.)

Things that only make sense with the sample services: the demo cases that were seeded into a new database, and the old "Quality" eval pages that score the made-up packets.
