import gpxpy
import gpxpy.gpx

def create_gpx(activity_meta):
    activity_ids = activity_meta['id']
    # types = ['time', 'distance', 'latlng', 'altitude', 'velocity_smooth', 'moving', 'grade_smooth', 'heartrate']
    types = ['time', 'latlng', 'altitude']
    for thisid in activity_ids:
        activity_data=client.get_activity_streams(thisid, types=types)
        # get start time for this activity
        starttime = activity_meta[activity_meta['id'] == thisid]['start_date'].values[0]

        ### Create gpx output
        gpx = gpxpy.gpx.GPX()

        # Create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for i in range(len(activity_data['time'].data)):
            lat = activity_data['latlng'].data[i][0]
            lon = activity_data['latlng'].data[i][1]
            ele = activity_data['altitude'].data[i]
            ts = pd.to_datetime(starttime) + datetime.timedelta(0, activity_data['time'].data[i])
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele, time=ts))

        filename = "strava_id_" + str(thisid) + ".gpx"
        with open(filename, "w") as f:
            f.write( gpx.to_xml())
        print("Generated file " + filename)
