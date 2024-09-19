# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import numpy as np
import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine(r"sqlite:///C:/Users/Leo/Desktop/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(autoload_with=engine)


# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station


#################################################
# Flask Setup
#################################################

app = Flask(__name__)

def get_last_and_one_year():
    session = Session(engine)
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    last_date = dt.datetime.strptime(last_date, '%Y-%m-%d')
    one_year = last_date - dt.timedelta(days=365)
    session.close()
    return last_date, one_year


#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months."""
    
    # Get the last date and one year ago date
    last_date, one_year = get_last_and_one_year()

    # Create a session to connect to the database
    session = Session(engine)

    # Query precipitation data for the last 12 months
    results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year).all()

    # Close the session
    session.close()

    # Convert query results to dictionary format {date: prcp}
    precipitation_dict = {date: prcp for date, prcp in results}

    # Return the dictionary as JSON
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations."""
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()

    # Convert list of tuples into a normal list
    stations_list = list(np.ravel(results))
    
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature observations for the last year from the most active station."""
    session = Session(engine)

    # Find the most active station
    most_active_station = session.query(Measurement.station).group_by(Measurement.station)\
                                .order_by(func.count(Measurement.station).desc()).first()[0]

    # Query the temperature observations (tobs) for the most active station in the last year
    last_date, one_year = get_last_and_one_year()
    results = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station)\
                            .filter(Measurement.date >= one_year).all()
    session.close()

    # Convert list of tuples into normal list
    tobs_list = [{date: tobs} for date, tobs in results]
    
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
def temperature_from_start(start):
    """Return TMIN, TAVG, TMAX for all dates greater than or equal to the start date."""
    
    # Create a session to connect to the database
    session = Session(engine)

    # Query for TMIN, TAVG, and TMAX from the start date onwards
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start).all()

    # Close the session after querying
    session.close()

    # If no results were found, return an error message
    if not results or results == [(None, None, None)]:
        return jsonify({"error": f"No data found from {start} onwards."})

    # Convert the query result into a dictionary
    temps = list(np.ravel(results))
    temp_dict = {
        "TMIN": temps[0],
        "TAVG": temps[1],
        "TMAX": temps[2]
    }

    # Return the dictionary as a JSON response
    return jsonify(temp_dict)

@app.route("/api/v1.0/<start>/<end>")
def temperature_from_start_to_end(start, end):
    """Return TMIN, TAVG, TMAX for the specified start and end date range."""

    # Create a session to connect to the database
    session = Session(engine)

    # Query for TMIN, TAVG, and TMAX between the start and end dates
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    # Close the session after querying
    session.close()

    # If no results were found, return an error message
    if not results or results == [(None, None, None)]:
        return jsonify({"error": f"No data found for the range {start} to {end}."})

    # Convert the query result into a dictionary
    temps = list(np.ravel(results))
    temp_dict = {
        "TMIN": temps[0],
        "TAVG": temps[1],
        "TMAX": temps[2]
    }

    # Return the dictionary as a JSON response
    return jsonify(temp_dict)


if __name__ == '__main__':
    app.run(debug=True)
