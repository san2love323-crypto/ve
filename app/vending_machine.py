from app.data.models import CouponModel, TxModel


class VendingMachine:
    def __init__(self):
        self.coupon = CouponModel()
        self.tx = TxModel()
        self.coupon.create_table()
        self.tx.create_table()

    def user_balance(self, user_id: str) -> int:
        return self.tx.view_balance(user_id)

    def view_showcase(self) -> list:
        return self.coupon.show_coupons()

    def add_coupon(self, description: str, code: str, cost: int) -> str:
        return self.coupon.insert_model(description, code, cost)

    def give_credit(self, user_id: str, value: int):
        return self.tx.insert_model(user_id, value)

    def buy_coupon(self, user_id: str, coupon_id: int):
        """
        성공: ('ok', 메시지, 쿠폰코드)
        실패: ('err', 메시지)
        """
        coupon = self.coupon.get_coupon(coupon_id)
        if coupon is None:
            return ('err', '존재하지 않는 쿠폰입니다.')

        code, cost = coupon
        if self.tx.view_balance(user_id) < cost:
            return ('err', '크레딧이 부족합니다.')

        status, message = self.tx.insert_model(user_id, cost, int(coupon_id))
        if status != 'ok':
            return ('err', message)
        return ('ok', '구매가 완료되었습니다. 쿠폰 코드는 DM으로 보냈습니다.', code)
