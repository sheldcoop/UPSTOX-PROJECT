"""
Input Validation Schemas using Marshmallow
"""

from marshmallow import Schema, fields, validate, ValidationError


class OrderSchema(Schema):
    """Validation schema for order placement"""

    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    quantity = fields.Int(required=True, validate=validate.Range(min=1, max=10000))
    price = fields.Float(required=True, validate=validate.Range(min=0.01))
    order_type = fields.Str(
        required=True, validate=validate.OneOf(["MARKET", "LIMIT", "SL", "SL-M"])
    )
    transaction_type = fields.Str(
        required=True, validate=validate.OneOf(["BUY", "SELL"])
    )
    product = fields.Str(
        required=True, validate=validate.OneOf(["INTRADAY", "DELIVERY", "MTF"])
    )


class SymbolSchema(Schema):
    """Validation schema for symbol queries"""

    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    exchange = fields.Str(validate=validate.OneOf(["NSE", "BSE", "NFO", "BFO", "MCX"]))


class DateRangeSchema(Schema):
    """Validation schema for date range queries"""

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)

    def validate_date_range(self, data, **kwargs):
        if data["end_date"] < data["start_date"]:
            raise ValidationError("end_date must be after start_date")


class AlertRuleSchema(Schema):
    """Validation schema for creating alert rules"""

    symbol = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    alert_type = fields.Str(
        required=True, validate=validate.OneOf(["PRICE", "VOLUME", "RSI", "MACD"])
    )
    condition = fields.Str(
        required=True,
        validate=validate.OneOf(["ABOVE", "BELOW", "CROSSES_ABOVE", "CROSSES_BELOW"]),
    )
    threshold = fields.Float(required=True)
    is_active = fields.Bool(missing=True)


class StrategyConfigSchema(Schema):
    """Validation schema for strategy configuration"""

    strategy_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    symbols = fields.List(fields.Str(), required=True, validate=validate.Length(min=1))
    timeframe = fields.Str(
        required=True, validate=validate.OneOf(["1m", "5m", "15m", "30m", "1h", "1d"])
    )
    risk_percent = fields.Float(validate=validate.Range(min=0.1, max=10.0))
    max_positions = fields.Int(validate=validate.Range(min=1, max=50))


class PortfolioQuerySchema(Schema):
    """Validation schema for portfolio queries"""

    mode = fields.Str(validate=validate.OneOf(["live", "paper"]))
    include_holdings = fields.Bool(missing=True)
    include_positions = fields.Bool(missing=True)


def validate_request_data(schema_class, data):
    """
    Validate request data against a schema

    Args:
        schema_class: Marshmallow schema class
        data: Dict of data to validate

    Returns:
        Validated data dict

    Raises:
        ValidationError: If validation fails
    """
    schema = schema_class()
    return schema.load(data)


def safe_validate(schema_class, data):
    """
    Safe validation that returns (data, errors) tuple

    Args:
        schema_class: Marshmallow schema class
        data: Dict of data to validate

    Returns:
        Tuple of (validated_data or None, errors or None)
    """
    schema = schema_class()
    try:
        validated = schema.load(data)
        return validated, None
    except ValidationError as e:
        return None, e.messages
