# api/routes/payments.py
from flask import Blueprint, request, jsonify
from api.services.payments_service import PagoService
from api.routes.auth_bp import jwt_required
from datetime import datetime, timedelta

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/', methods=['GET'])
@jwt_required
def obtener_pagos():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id es requerido"}), 400
        
    try:
        pagos = PagoService.obtener_por_usuario(user_id)
        return jsonify(pagos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@payments_bp.route('/', methods=['POST'])
@jwt_required
def crear_pago():
    try:
        data = request.get_json()
        required_fields = ['user_id', 'amount', 'method']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        pago = PagoService.crear_pago(data)
        return jsonify(pago), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@payments_bp.route('/<pago_id>/confirm', methods=['POST'])
@jwt_required
def confirmar_pago(pago_id):
    try:
        pago = PagoService.actualizar_estado(pago_id, 'paid')
        if not pago:
            return jsonify({"error": "Pago no encontrado"}), 404
            
        return jsonify({
            "message": "Pago confirmado y cuenta activada",
            "pago": pago
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@payments_bp.route('/check-active/<user_id>', methods=['GET'])
@jwt_required
def verificar_pago_activo(user_id):
    try:
        activo = PagoService.verificar_pago_activo(user_id)
        return jsonify({"active": activo})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
