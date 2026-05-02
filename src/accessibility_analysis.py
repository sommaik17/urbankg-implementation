#!/usr/bin/env python3
"""
Service Accessibility Analysis for UrbanKG
Implements the 15-minute city accessibility metrics from Section 6.4

Metrics computed:
1. Transit-Based Accessibility (TBA)
2. Service Coverage Index (SCI)
3. Multi-Modal Accessibility Score (MMAS)

Authors: Sommai Khantong, Charuay Savithi, Mohammad Nazir Ahmad
License: MIT
"""

import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, GEO
from SPARQLWrapper import SPARQLWrapper, JSON
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import math

# Namespace definitions
URB = Namespace("http://urbankg.org/ontology#")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
GEOF = Namespace("http://www.opengis.net/def/function/geosparql/")

@dataclass
class AccessibilityMetrics:
    """Container for accessibility metrics"""
    district_id: str
    district_name: str
    transit_stops_per_km2: float
    hospital_access_pct: float
    govt_access_pct: float
    env_quality: str
    mmas_score: float

class AccessibilityAnalyzer:
    """
    Implements the Service Accessibility and Coverage Analysis
    from Section 6.4 of the UrbanKG paper
    """
    
    def __init__(self, sparql_endpoint: str):
        """
        Initialize analyzer with SPARQL endpoint
        
        Args:
            sparql_endpoint: URL of the SPARQL endpoint
        """
        self.sparql = SPARQLWrapper(sparql_endpoint)
        self.sparql.setReturnFormat(JSON)
        
        # Constants from paper (Section 6.4)
        self.ACCESSIBILITY_THRESHOLD_M = 2000  # 15-minute transit catchment
        self.WALKING_SPEED_KMH = 4.0  # meters per hour
        self.TRANSIT_SPEED_KMH = 8.0  # average km/h
        self.WHO_PM25_THRESHOLD = 35.0  # μg/m³
        
        # Weights for MMAS calculation (from paper)
        self.MMAS_WEIGHTS = {
            'hospital': 0.30,
            'emergency': 0.30,
            'government': 0.20,
            'facility': 0.15,
            'environment': 0.05
        }
    
    def calculate_transit_based_accessibility(self, 
                                              district_uri: str, 
                                              time_threshold_min: int = 15) -> float:
        """
        Calculate Transit-Based Accessibility (TBA) for a district
        
        TBA(d,t) = Area(R_{d,t}) / Area(d)
        
        Args:
            district_uri: URI of the district
            time_threshold_min: Time threshold in minutes (default: 15)
            
        Returns:
            TBA score (0.0-1.0)
        """
        query = f"""
        PREFIX urb: <http://urbankg.org/ontology#>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
        
        SELECT ?stop ?stopGeom
        WHERE {{
            <{district_uri}> a urb:District ;
                            geo:hasGeometry ?districtGeom .
            
            ?stop a urb:TransitStop ;
                  geo:hasGeometry ?stopGeom .
            
            FILTER(geof:sfWithin(?stopGeom, ?districtGeom))
        }}
        """
        
        self.sparql.setQuery(query)
        results = self.sparql.query().convert()
        
        # Calculate reachable area from transit stops
        # Simplified: count stops and assume coverage
        num_stops = len(results["results"]["bindings"])
        
        # Estimate: each stop covers ~π * (2km)² ≈ 12.57 km²
        coverage_per_stop_km2 = math.pi * (self.ACCESSIBILITY_THRESHOLD_M / 1000) ** 2
        
        # This is a simplified calculation
        # Production implementation would use actual geometric union
        return min(1.0, num_stops * coverage_per_stop_km2 / 100.0)
    
    def calculate_service_coverage_index(self,
                                         district_uri: str,
                                         service_type: str,
                                         population: int) -> float:
        """
        Calculate Service Coverage Index (SCI) for a district
        
        SCI(d,s) = |{p ∈ S_s : distance(d,p) ≤ θ}| / Population(d)
        
        Args:
            district_uri: URI of the district
            service_type: Type of service (Hospital, GovernmentOffice, etc.)
            population: District population
            
        Returns:
            SCI per 10,000 residents
        """
        query = f"""
        PREFIX urb: <http://urbankg.org/ontology#>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
        
        SELECT (COUNT(DISTINCT ?service) AS ?count)
        WHERE {{
            <{district_uri}> geo:hasGeometry ?districtGeom .
            
            ?service a urb:{service_type} ;
                    geo:hasGeometry ?serviceGeom .
            
            FILTER(geof:distance(?districtGeom, ?serviceGeom,
                   <http://www.opengis.net/def/uom/OGC/1.0/metre>) 
                   <= {self.ACCESSIBILITY_THRESHOLD_M})
        }}
        """
        
        self.sparql.setQuery(query)
        results = self.sparql.query().convert()
        
        count = int(results["results"]["bindings"][0]["count"]["value"])
        
        # Return per 10,000 residents
        return (count / population) * 10000 if population > 0 else 0.0
    
    def calculate_hospital_accessibility_percentage(self, 
                                                    district_uri: str) -> float:
        """
        Calculate percentage hospital accessibility via transit
        Uses the complete SPARQL query from Section 6.4
        
        Args:
            district_uri: URI of the district
            
        Returns:
            Percentage (0-100) of hospitals accessible within threshold
        """
        query = f"""
        PREFIX urb: <http://urbankg.org/ontology#>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
        
        SELECT (COUNT(DISTINCT ?hospital) AS ?accessible)
               (COUNT(DISTINCT ?allHospital) AS ?total)
        WHERE {{
            <{district_uri}> geo:hasGeometry ?districtGeom .
            
            # Transit stops in district
            ?stop a urb:TransitStop ;
                  geo:hasGeometry ?stopGeom .
            FILTER(geof:sfWithin(?stopGeom, ?districtGeom))
            
            # Accessible hospitals
            ?hospital a urb:Hospital ;
                     geo:hasGeometry ?hospitalGeom .
            FILTER(geof:distance(?stopGeom, ?hospitalGeom,
                   <http://www.opengis.net/def/uom/OGC/1.0/metre>)
                   <= {self.ACCESSIBILITY_THRESHOLD_M})
            
            # Total hospitals in city
            {{
                SELECT ?allHospital
                WHERE {{ ?allHospital a urb:Hospital }}
            }}
        }}
        """
        
        self.sparql.setQuery(query)
        results = self.sparql.query().convert()
        
        binding = results["results"]["bindings"][0]
        accessible = int(binding["accessible"]["value"])
        total = int(binding["total"]["value"])
        
        return (accessible / total * 100) if total > 0 else 0.0
    
    def calculate_mmas(self, 
                      hospital_score: float,
                      emergency_score: float,
                      govt_score: float,
                      facility_score: float,
                      env_score: float) -> float:
        """
        Calculate Multi-Modal Accessibility Score (MMAS)
        
        MMAS = 0.30×S_hospital + 0.30×S_emergency + 0.20×S_govt 
               + 0.15×S_facility + 0.05×S_env
        
        Args:
            hospital_score: Hospital accessibility (0-10)
            emergency_score: Emergency service accessibility (0-10)
            govt_score: Government office accessibility (0-10)
            facility_score: Public facility accessibility (0-10)
            env_score: Environmental quality score (0-10)
            
        Returns:
            MMAS score (0-10)
        """
        return (
            self.MMAS_WEIGHTS['hospital'] * hospital_score +
            self.MMAS_WEIGHTS['emergency'] * emergency_score +
            self.MMAS_WEIGHTS['government'] * govt_score +
            self.MMAS_WEIGHTS['facility'] * facility_score +
            self.MMAS_WEIGHTS['environment'] * env_score
        )
    
    def calculate_response_time(self,
                               transit_frequency: float,
                               distance_m: float) -> float:
        """
        Calculate average emergency response time via transit
        From Section 6.4: Response Time Computation
        
        Components:
        1. Access walk time: 5 minutes (fixed)
        2. Average wait time: 60 / (2 × frequency)
        3. Transit travel time: distance / 133.33 m/min
        4. Egress walk time: 2 minutes (fixed)
        
        Args:
            transit_frequency: Trips per hour
            distance_m: Distance from stop to hospital in meters
            
        Returns:
            Total response time in minutes
        """
        ACCESS_WALK_MIN = 5.0
        EGRESS_WALK_MIN = 2.0
        TRANSIT_SPEED_M_PER_MIN = 133.33  # 8 km/h
        
        wait_time = 60 / (2 * transit_frequency) if transit_frequency > 0 else 30
        transit_time = distance_m / TRANSIT_SPEED_M_PER_MIN
        
        return ACCESS_WALK_MIN + wait_time + transit_time + EGRESS_WALK_MIN
    
    def analyze_district(self, 
                        district_uri: str,
                        district_name: str,
                        population: int,
                        area_km2: float) -> AccessibilityMetrics:
        """
        Perform complete accessibility analysis for a district
        
        Args:
            district_uri: URI of the district
            district_name: Human-readable district name
            population: District population
            area_km2: District area in square kilometers
            
        Returns:
            AccessibilityMetrics object with all computed metrics
        """
        # Calculate transit density
        transit_stops = self._count_transit_stops(district_uri)
        transit_density = transit_stops / area_km2 if area_km2 > 0 else 0.0
        
        # Calculate hospital accessibility
        hospital_access = self.calculate_hospital_accessibility_percentage(
            district_uri
        )
        
        # Calculate government office accessibility
        govt_access = self.calculate_service_coverage_index(
            district_uri, "GovernmentOffice", population
        )
        
        # Get environmental quality
        env_quality = self._get_environmental_quality(district_uri)
        
        # Calculate component scores (normalized to 0-10)
        hospital_score = (hospital_access / 100) * 10
        govt_score = min(10, govt_access)  # Normalized
        env_score = self._env_quality_to_score(env_quality)
        
        # Simplified scores for emergency and facility
        # (would be calculated similarly in production)
        emergency_score = hospital_score * 0.9  # Approximate
        facility_score = govt_score * 0.8  # Approximate
        
        # Calculate MMAS
        mmas = self.calculate_mmas(
            hospital_score, emergency_score, govt_score,
            facility_score, env_score
        )
        
        return AccessibilityMetrics(
            district_id=district_uri,
            district_name=district_name,
            transit_stops_per_km2=transit_density,
            hospital_access_pct=hospital_access,
            govt_access_pct=govt_access,
            env_quality=env_quality,
            mmas_score=round(mmas, 1)
        )
    
    def _count_transit_stops(self, district_uri: str) -> int:
        """Helper: Count transit stops in district"""
        query = f"""
        PREFIX urb: <http://urbankg.org/ontology#>
        
        SELECT (COUNT(?stop) AS ?count)
        WHERE {{
            ?stop a urb:TransitStop ;
                  urb:locatedInDistrict <{district_uri}> .
        }}
        """
        self.sparql.setQuery(query)
        results = self.sparql.query().convert()
        return int(results["results"]["bindings"][0]["count"]["value"])
    
    def _get_environmental_quality(self, district_uri: str) -> str:
        """Helper: Get environmental quality classification"""
        # Simplified - would query PM2.5 levels in production
        return "Moderate"
    
    def _env_quality_to_score(self, quality: str) -> float:
        """Helper: Convert environmental quality to 0-10 score"""
        mapping = {"Good": 8.0, "Moderate": 5.0, "Poor": 2.0}
        return mapping.get(quality, 5.0)

def main():
    """Example usage"""
    analyzer = AccessibilityAnalyzer("http://localhost:3030/urbankg/sparql")
    
    # Analyze sample district
    metrics = analyzer.analyze_district(
        district_uri="http://urbankg.org/ontology#District_Central",
        district_name="District 1",
        population=150000,
        area_km2=25.0
    )
    
    print(f"Accessibility Analysis Results for {metrics.district_name}")
    print(f"Transit Density: {metrics.transit_stops_per_km2:.1f} stops/km²")
    print(f"Hospital Access: {metrics.hospital_access_pct:.0f}%")
    print(f"Government Access: {metrics.govt_access_pct:.0f}%")
    print(f"Environmental Quality: {metrics.env_quality}")
    print(f"MMAS Score: {metrics.mmas_score}")

if __name__ == "__main__":
    main()
