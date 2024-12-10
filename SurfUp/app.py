
from flask import Flask, jsonify
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

# Database setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask app setup
app = Flask(__name__)

# Homepage route
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Welcome to the Climate App API!<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Retrieve the last 12 months of precipitation data."""
    session = Session(engine)
    # Find the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Query precipitation data
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    session.close()

    # Convert to dictionary
    precipitation_dict = {date: prcp for date, prcp in results}
    return jsonify(precipitation_dict)

# Stations route
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations."""
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    # Unpack results into a list
    stations_list = [station[0] for station in results]
    return jsonify(stations_list)

# TOBS route
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station for the last year."""
    session = Session(engine)
    # Find the most active station
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Find the most recent date and calculate the date one year ago
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Query temperature observations
    results = session.query(Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago).all()
    session.close()

    # Unpack results into a list
    tobs_list = [tobs[0] for tobs in results]
    return jsonify(tobs_list)

# Start and Start/End range route
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    """Return TMIN, TAVG, and TMAX for a specified start or start-end range."""
    session = Session(engine)

    # Convert start and end dates to datetime
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    if end:
        end_date = dt.datetime.strptime(end, "%Y-%m-%d")

    # Query temperature statistics
    if end:
        results = session.query(func.min(Measurement.tobs),
                                func.avg(Measurement.tobs),
                                func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).\
            filter(Measurement.date <= end_date).all()
    else:
        results = session.query(func.min(Measurement.tobs),
                                func.avg(Measurement.tobs),
                                func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).all()
    session.close()

    # Unpack results into a dictionary
    temp_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }
    return jsonify(temp_stats)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
