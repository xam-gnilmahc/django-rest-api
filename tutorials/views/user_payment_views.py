from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from tutorials.models.user_payment_gateway import UserPaymentGateway
from tutorials.serializers.payment_gateway_serializer import UserPaymentGatewaySerializer
from tutorials.utils.response_helper import success_response, error_response

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def userPaymentGateway_list(request):
    if request.method == 'GET':
        user_id = request.query_params.get('userId')
        payment_gateways = UserPaymentGateway.objects.all()
        if user_id:
            payment_gateways = payment_gateways.filter(user_id=user_id)

        serializer = UserPaymentGatewaySerializer(payment_gateways, many=True)
        return success_response('Payment gateways fetched successfully.', serializer.data)

    elif request.method == 'POST':
        data = request.data.copy()
        data['created_by'] = request.user.id 
        data['updated_by'] = request.user.id  

        serializer = UserPaymentGatewaySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return success_response('Payment gateway added successfully.', serializer.data, status.HTTP_201_CREATED)
        return error_response('Validation failed.', serializer.errors)