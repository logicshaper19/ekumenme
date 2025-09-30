"""
Evapotranspiration Service - FAO-56 Penman-Monteith Implementation

This is a DOMAIN SERVICE for agricultural evapotranspiration calculations.
Not a generic utility - this is core agricultural science.

Implements:
1. Solar radiation estimation from temperature and cloud cover
2. Reference evapotranspiration (ET₀) using Penman-Monteith FAO-56
3. Crop evapotranspiration (ETc) using crop coefficients

References:
- Allen et al. (1998) FAO Irrigation and Drainage Paper No. 56
- Chapter 3: Meteorological data
- Chapter 4: Determination of ET₀
"""

import math
from datetime import datetime
from typing import Tuple, Optional


class SolarRadiationEstimator:
    """
    Estimate solar radiation from temperature range and cloud cover
    Using FAO-56 methods when direct measurements unavailable
    """
    
    @staticmethod
    def julian_day(date: datetime) -> int:
        """Calculate Julian day (1-365/366)"""
        return date.timetuple().tm_yday
    
    @staticmethod
    def solar_declination(julian_day: int) -> float:
        """
        Calculate solar declination (δ) in radians
        FAO-56 Eq. 24
        """
        return 0.409 * math.sin((2 * math.pi * julian_day / 365) - 1.39)
    
    @staticmethod
    def sunset_hour_angle(latitude_rad: float, solar_decl: float) -> float:
        """
        Calculate sunset hour angle (ωs) in radians
        FAO-56 Eq. 25
        """
        return math.acos(-math.tan(latitude_rad) * math.tan(solar_decl))
    
    @staticmethod
    def inverse_relative_distance(julian_day: int) -> float:
        """
        Calculate inverse relative distance Earth-Sun (dr)
        FAO-56 Eq. 23
        """
        return 1 + 0.033 * math.cos(2 * math.pi * julian_day / 365)
    
    @staticmethod
    def extraterrestrial_radiation(
        latitude_deg: float,
        julian_day: int
    ) -> float:
        """
        Calculate extraterrestrial radiation (Ra) in MJ/m²/day
        FAO-56 Eq. 21
        
        Args:
            latitude_deg: Latitude in degrees (positive N, negative S)
            julian_day: Day of year (1-365)
        
        Returns:
            Ra in MJ/m²/day
        """
        # Convert latitude to radians
        lat_rad = latitude_deg * math.pi / 180
        
        # Solar parameters
        delta = SolarRadiationEstimator.solar_declination(julian_day)
        dr = SolarRadiationEstimator.inverse_relative_distance(julian_day)
        ws = SolarRadiationEstimator.sunset_hour_angle(lat_rad, delta)
        
        # Solar constant
        Gsc = 0.0820  # MJ/m²/min
        
        # Calculate Ra
        Ra = (24 * 60 / math.pi) * Gsc * dr * (
            ws * math.sin(lat_rad) * math.sin(delta) +
            math.cos(lat_rad) * math.cos(delta) * math.sin(ws)
        )
        
        return Ra
    
    @staticmethod
    def clear_sky_radiation(
        Ra: float,
        elevation_m: float = 0
    ) -> float:
        """
        Calculate clear-sky solar radiation (Rso) in MJ/m²/day
        FAO-56 Eq. 37 (simplified for missing data)
        
        Args:
            Ra: Extraterrestrial radiation (MJ/m²/day)
            elevation_m: Station elevation (meters)
        
        Returns:
            Rso in MJ/m²/day
        """
        return (0.75 + 2e-5 * elevation_m) * Ra
    
    @staticmethod
    def estimate_from_temperature(
        temp_min: float,
        temp_max: float,
        latitude_deg: float,
        date: datetime,
        elevation_m: float = 0
    ) -> float:
        """
        Estimate solar radiation from temperature range (Hargreaves method)
        FAO-56 Eq. 50
        
        Args:
            temp_min: Minimum temperature (°C)
            temp_max: Maximum temperature (°C)
            latitude_deg: Latitude (degrees)
            date: Date for calculation
            elevation_m: Elevation (meters)
        
        Returns:
            Estimated Rs in MJ/m²/day
        """
        j_day = SolarRadiationEstimator.julian_day(date)
        Ra = SolarRadiationEstimator.extraterrestrial_radiation(
            latitude_deg, j_day
        )
        
        # Hargreaves coefficient (typical value 0.16-0.19)
        kRs = 0.17
        
        # Estimate Rs
        Rs = kRs * math.sqrt(temp_max - temp_min) * Ra
        
        return Rs
    
    @staticmethod
    def estimate_from_cloud_cover(
        Ra: float,
        cloud_cover_percent: float,
        elevation_m: float = 0
    ) -> float:
        """
        Estimate solar radiation from cloud cover
        FAO-56 Eq. 35 (Angstrom formula)
        
        Args:
            Ra: Extraterrestrial radiation (MJ/m²/day)
            cloud_cover_percent: Cloud cover (0-100%)
            elevation_m: Elevation (meters)
        
        Returns:
            Estimated Rs in MJ/m²/day
        """
        # Angstrom coefficients (typical values)
        as_coef = 0.25  # Fraction on overcast day
        bs_coef = 0.50  # Additional fraction on clear day
        
        # Sunshine ratio (n/N) from cloud cover
        n_N = 1 - (cloud_cover_percent / 100)
        
        # Calculate Rs
        Rs = (as_coef + bs_coef * n_N) * Ra
        
        return Rs
    
    @staticmethod
    def estimate_best_available(
        temp_min: float,
        temp_max: float,
        latitude_deg: float,
        date: datetime,
        cloud_cover_percent: Optional[float] = None,
        elevation_m: float = 0
    ) -> Tuple[float, str]:
        """
        Estimate solar radiation using best available method
        
        Returns:
            Tuple of (Rs in MJ/m²/day, method_used)
        """
        j_day = SolarRadiationEstimator.julian_day(date)
        Ra = SolarRadiationEstimator.extraterrestrial_radiation(
            latitude_deg, j_day
        )
        
        # Method 1: Cloud cover (more accurate if available)
        if cloud_cover_percent is not None:
            Rs = SolarRadiationEstimator.estimate_from_cloud_cover(
                Ra, cloud_cover_percent, elevation_m
            )
            method = "cloud_cover"
        
        # Method 2: Temperature range (fallback)
        else:
            Rs = SolarRadiationEstimator.estimate_from_temperature(
                temp_min, temp_max, latitude_deg, date, elevation_m
            )
            method = "temperature_range"
        
        # Validate: Rs should not exceed clear-sky radiation
        Rso = SolarRadiationEstimator.clear_sky_radiation(Ra, elevation_m)
        if Rs > Rso:
            Rs = Rso
        
        return Rs, method


class PenmanMonteithET0:
    """
    Calculate reference evapotranspiration (ET₀) using Penman-Monteith FAO-56
    """
    
    @staticmethod
    def saturation_vapor_pressure(temp_c: float) -> float:
        """
        Calculate saturation vapor pressure (es) in kPa
        FAO-56 Eq. 11
        """
        return 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    
    @staticmethod
    def actual_vapor_pressure(temp_min: float, humidity_mean: float) -> float:
        """
        Calculate actual vapor pressure (ea) in kPa
        FAO-56 Eq. 19 (from Tmin and RHmean)
        """
        es_tmin = PenmanMonteithET0.saturation_vapor_pressure(temp_min)
        return es_tmin * (humidity_mean / 100)
    
    @staticmethod
    def slope_vapor_pressure_curve(temp_c: float) -> float:
        """
        Calculate slope of saturation vapor pressure curve (Δ) in kPa/°C
        FAO-56 Eq. 13
        """
        return (4098 * 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))) / \
               ((temp_c + 237.3) ** 2)
    
    @staticmethod
    def psychrometric_constant(elevation_m: float = 0) -> float:
        """
        Calculate psychrometric constant (γ) in kPa/°C
        FAO-56 Eq. 8
        """
        # Atmospheric pressure from elevation
        P = 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26
        return 0.000665 * P
    
    @staticmethod
    def net_radiation(
        Rs: float,
        temp_min: float,
        temp_max: float,
        humidity_mean: float,
        latitude_deg: float,
        date: datetime,
        elevation_m: float = 0
    ) -> float:
        """
        Calculate net radiation (Rn) in MJ/m²/day
        FAO-56 Eq. 40
        """
        # Net shortwave radiation (FAO-56 Eq. 38)
        albedo = 0.23  # Reference crop albedo
        Rns = (1 - albedo) * Rs
        
        # Net longwave radiation (FAO-56 Eq. 39)
        temp_mean_k = (temp_max + temp_min) / 2 + 273.16
        temp_max_k = temp_max + 273.16
        temp_min_k = temp_min + 273.16
        
        # Stefan-Boltzmann constant
        sigma = 4.903e-9  # MJ/K⁴/m²/day
        
        # Actual vapor pressure
        ea = PenmanMonteithET0.actual_vapor_pressure(temp_min, humidity_mean)
        
        # Clear sky radiation
        j_day = SolarRadiationEstimator.julian_day(date)
        Ra = SolarRadiationEstimator.extraterrestrial_radiation(
            latitude_deg, j_day
        )
        Rso = SolarRadiationEstimator.clear_sky_radiation(Ra, elevation_m)
        
        # Net longwave radiation
        Rnl = sigma * (
            (temp_max_k ** 4 + temp_min_k ** 4) / 2
        ) * (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * Rs / Rso - 0.35)
        
        # Net radiation
        Rn = Rns - Rnl
        
        return Rn
    
    @staticmethod
    def calculate(
        temp_min: float,
        temp_max: float,
        humidity_mean: float,
        wind_speed_kmh: float,
        Rs: float,
        latitude_deg: float,
        date: datetime,
        elevation_m: float = 0
    ) -> float:
        """
        Calculate reference evapotranspiration (ET₀) in mm/day
        FAO-56 Eq. 6 (Penman-Monteith)
        
        Args:
            temp_min: Minimum temperature (°C)
            temp_max: Maximum temperature (°C)
            humidity_mean: Mean relative humidity (%)
            wind_speed_kmh: Wind speed at 2m (km/h)
            Rs: Solar radiation (MJ/m²/day)
            latitude_deg: Latitude (degrees)
            date: Date for calculation
            elevation_m: Elevation (meters)
        
        Returns:
            ET₀ in mm/day
        """
        # Convert wind speed from km/h to m/s
        wind_speed_ms = wind_speed_kmh / 3.6
        
        # Mean temperature
        temp_mean = (temp_max + temp_min) / 2
        
        # Vapor pressure deficit
        es_tmax = PenmanMonteithET0.saturation_vapor_pressure(temp_max)
        es_tmin = PenmanMonteithET0.saturation_vapor_pressure(temp_min)
        es = (es_tmax + es_tmin) / 2
        ea = PenmanMonteithET0.actual_vapor_pressure(temp_min, humidity_mean)
        vpd = es - ea
        
        # Slope of saturation vapor pressure curve
        delta = PenmanMonteithET0.slope_vapor_pressure_curve(temp_mean)
        
        # Psychrometric constant
        gamma = PenmanMonteithET0.psychrometric_constant(elevation_m)
        
        # Net radiation
        Rn = PenmanMonteithET0.net_radiation(
            Rs, temp_min, temp_max, humidity_mean,
            latitude_deg, date, elevation_m
        )
        
        # Soil heat flux (negligible for daily calculations)
        G = 0
        
        # Penman-Monteith equation (FAO-56 Eq. 6)
        numerator = (
            0.408 * delta * (Rn - G) +
            gamma * (900 / (temp_mean + 273)) * wind_speed_ms * vpd
        )
        denominator = delta + gamma * (1 + 0.34 * wind_speed_ms)
        
        ET0 = numerator / denominator
        
        # Ensure non-negative
        return max(0, ET0)

