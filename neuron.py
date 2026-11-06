import math
import config


class Neuron:
    def __init__(self, w1=config.DEFAULT_W1, w2=config.DEFAULT_W2, bias=config.DEFAULT_BIAS):
        self.w1 = w1
        self.w2 = w2
        self.bias = bias
        self.consecutive_on = 0
        self.consecutive_off = 0
        self.alert_state = False

    def predict(self, x1, x2):
        z = (x1 * self.w1) + (x2 * self.w2) + self.bias
        alerta_raw = z >= 0

        if alerta_raw:
            self.consecutive_on += 1
            self.consecutive_off = 0
            if self.consecutive_on >= config.ALERT_ON_SAMPLES:
                self.alert_state = True
        else:
            self.consecutive_off += 1
            self.consecutive_on = 0
            if self.consecutive_off >= config.ALERT_OFF_SAMPLES:
                self.alert_state = False

        return z, self.alert_state

    def set_weights(self, w1=None, w2=None, bias=None):
        if w1 is not None:
            parsed = self._parse_number(w1, config.W_LIMIT)
            if parsed is not None:
                self.w1 = parsed
        if w2 is not None:
            parsed = self._parse_number(w2, config.W_LIMIT)
            if parsed is not None:
                self.w2 = parsed
        if bias is not None:
            parsed = self._parse_number(bias, config.W_LIMIT)
            if parsed is not None:
                self.bias = parsed

    def _parse_number(self, value, limit):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(number) or math.isinf(number):
            return None
        return max(-limit, min(limit, number))

    def get_params(self):
        return {"w1": self.w1, "w2": self.w2, "bias": self.bias}