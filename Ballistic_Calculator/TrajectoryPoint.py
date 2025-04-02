class TrajectoryPoint:
    """Класс, представляющий одну точку траектории пули."""
    
    def __init__(self, time,  x, y, z, distance, velocity, mach, drop, windage, energy):
        """
        :param time: Время с момента выстрела (с)
        :param x: Координата X (м) - Дальность
        :param y: Координата Y (м) - Высота
        :param z: Координата Z (м) - Боковое смещение
        :param distance: Пройденное расстояние (м)
        :param velocity: Текущая скорость (м/с)
        :param mach: Скорость в Махах (отношение к скорости звука)
        :param drop: Вертикальное отклонение (м)
        :param windage: Боковое отклонение (м)
        :param energy: Кинетическая энергия (Дж)
        :param optimal_game_weight: Оптимальный вес цели (кг)
        """
        self.time = time
        self.x = x
        self.y = y
        self.z = z
        self.distance = distance
        self.velocity = velocity
        self.mach = mach
        self.drop = drop
        self.windage = windage
        self.energy = energy

    def __repr__(self):
        return (f"TrajectoryPoint(time={self.time:.3f}s, distance={self.distance:.2f}m, velocity={self.velocity:.2f}m/s, "
                f"mach={self.mach:.2f}, drop={self.drop:.2f}m, windage={self.windage:.2f}m, energy={self.energy:.2f}J, ")
