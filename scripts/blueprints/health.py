#!/usr/bin/env python3
"""
Health & Status Blueprint
Handles health check endpoints
"""

from flask import Blueprint, jsonify, g
from datetime import datetime
import logging

health_bp = Blueprint("health", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }
    )
