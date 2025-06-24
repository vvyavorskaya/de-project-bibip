import os
import uuid
from typing import List, Optional, Tuple, Dict, Any, Union
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from decimal import Decimal
from datetime import datetime

RECORD_LENGTH = 500
LINE_RECORD_LENGTH = RECORD_LENGTH + 1 


class CarService:

    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        os.makedirs(self.root_directory_path, exist_ok=True)

        self.models_file = os.path.join(self.root_directory_path, "models.txt")
        self.models_index_file = os.path.join(self.root_directory_path, "models_index.txt")
        self.cars_file = os.path.join(self.root_directory_path, "cars.txt")
        self.cars_index_file = os.path.join(self.root_directory_path, "cars_index.txt")
        self.sales_file = os.path.join(self.root_directory_path, "sales.txt")
        self.sales_index_file = os.path.join(self.root_directory_path, "sales_index.txt")

        for file_path in [
            self.models_file, self.models_index_file,
            self.cars_file, self.cars_index_file,
            self.sales_file, self.sales_index_file
        ]:
            if not os.path.exists(file_path):
                open(file_path, 'w').close()

    def _get_entity_data_and_line_number(self, file_path: str, entity_id: str) -> Optional[Tuple[str, int]]:
        """Получает данные сущности и номер строки по ID"""
        index_file_path = self._get_index_file_path(file_path)

        line_number = self._find_line_number_in_index(index_file_path, entity_id) 
        if line_number is None:
            return None
        
        seek_position = line_number * LINE_RECORD_LENGTH
        with open(file_path, 'r') as f:
            f.seek(seek_position)
            line_content = f.read(RECORD_LENGTH).strip() 
            return line_content, line_number

    def _get_index_file_path(self, data_file_path: str) -> str:
        """Возвращает путь к индексному файлу для данного файла данных"""
        if data_file_path == self.models_file:
            return self.models_index_file
        elif data_file_path == self.cars_file:
            return self.cars_index_file
        elif data_file_path == self.sales_file:
            return self.sales_index_file
        else:
            raise ValueError("Неизвестный путь к файлу данных")

    def _write_record_and_update_index(self, file_path: str, index_file_path: str, entity_id: str, data: str) -> None:
        """Записывает данные в файл и обновляет индекс"""
        formatted_data = data.ljust(RECORD_LENGTH) 
        
        with open(file_path, 'a') as f:
            f.seek(0, os.SEEK_END)
            current_byte_offset = f.tell()
            line_number = current_byte_offset // LINE_RECORD_LENGTH
            
            f.write(formatted_data + '\n') 
        
        self._update_index(index_file_path, entity_id, line_number) 

    def _update_record_in_file(self, file_path: str, entity_id: str, new_data: str) -> None:
        """Обновляет запись в файле"""
        old_data_and_line_number = self._get_entity_data_and_line_number(file_path, entity_id)

        if old_data_and_line_number is None:
            raise ValueError(f"Сущность с ID {entity_id} не найдена для обновления.")

        old_line_content, line_number = old_data_and_line_number
        
        formatted_new_data = new_data.ljust(RECORD_LENGTH)
        
        if len(formatted_new_data) > RECORD_LENGTH: 
            raise ValueError(f"Новые данные для {entity_id} превышают максимальную длину записи {RECORD_LENGTH}.")

        seek_position = line_number * LINE_RECORD_LENGTH
        with open(file_path, 'r+') as f:
            f.seek(seek_position)
            f.write(formatted_new_data + '\n') 
            f.flush() 

    def _car_to_string(self, car: Car) -> str:
        """Преобразует объект Car в строку для записи в файл"""
        s = f"{car.vin}|{car.model}|{car.price}|{car.date_start.isoformat()}|{car.status.value}"
        return s.ljust(RECORD_LENGTH)

    def _string_to_car(self, data_string: str) -> Car:
        """Преобразует строку из файла в объект Car"""
        parts = data_string.strip().split('|')
        if len(parts) != 5: 
            raise ValueError(f"Неверный формат строки для автомобиля: {data_string}")
        
        return Car(
            vin=parts[0],
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus(parts[4])
        )

    def _model_to_string(self, model: Model) -> str:
        """Преобразует объект Model в строку для записи в файл"""
        prod_year = getattr(model, 'production_start_year', '')
        price = getattr(model, 'price', '')
        s = f"{model.id}|{model.name}|{model.brand}|{prod_year}|{price}"
        return s.ljust(RECORD_LENGTH)

    def _string_to_model(self, data_string: str) -> Model:
        """Преобразует строку из файла в объект Model"""
        parts = data_string.strip().split('|')
        if len(parts) < 3:
            raise ValueError(f"Неверный формат строки для модели: {data_string}")
        
        _id = int(parts[0])
        _name = parts[1]
        _brand = parts[2]
        
        model_obj = Model(id=_id, name=_name, brand=_brand)
        
        if len(parts) > 3 and parts[3]:
            try:
                setattr(model_obj, 'production_start_year', int(parts[3]))
            except ValueError:
                pass 
        
        if len(parts) > 4 and parts[4]:
            try:
                setattr(model_obj, 'price', float(parts[4]))
            except ValueError:
                pass 
        return model_obj

    def _sale_to_string(self, sale: Sale) -> str:
        """Преобразует объект Sale в строку для записи в файл"""
        s = f"{sale.sales_number}|{sale.car_vin}|{sale.sales_date.isoformat()}|{sale.cost}"
        return s.ljust(RECORD_LENGTH)

    def _string_to_sale(self, data_string: str) -> Sale:
        """Преобразует строку из файла в объект Sale"""
        parts = data_string.strip().split('|')
        if len(parts) != 4:
            raise ValueError(f"Неверный формат строки для продажи: {data_string}")
        
        return Sale(
            sales_number=parts[0],
            car_vin=parts[1],
            sales_date=datetime.fromisoformat(parts[2]),
            cost=Decimal(parts[3])
        )

    def _find_car_by_vin(self, vin: str) -> Optional[Car]:
        """Находит автомобиль по VIN"""
        car_data_and_line_number = self._get_entity_data_and_line_number(self.cars_file, vin)
        if car_data_and_line_number:
            car_string, _ = car_data_and_line_number
            return self._string_to_car(car_string)
        return None

    def _update_car_status_or_data(self, car: Car) -> None:
        """Обновляет статус или данные автомобиля"""
        self._update_record_in_file(self.cars_file, car.vin, self._car_to_string(car))

    def sell_car(self, sale: Sale) -> Sale:
        """Продает автомобиль (исправленная версия для работы с тестами)"""
        if not isinstance(sale, Sale):
            raise ValueError("Метод sell_car ожидает объект Sale")
            
        car = self._find_car_by_vin(sale.car_vin)

        if not car:
            raise ValueError(f"Автомобиль с VIN {sale.car_vin} не найден.")
        
        if car.status == CarStatus.sold:
            raise ValueError(f"Автомобиль с VIN {sale.car_vin} уже продан.")

        car.status = CarStatus.sold
        self._update_car_status_or_data(car)

        self._write_record_and_update_index(
            self.sales_file, 
            self.sales_index_file, 
            sale.sales_number, 
            self._sale_to_string(sale))
        
        return sale

    def _find_line_number_in_index(self, index_file_path: str, entity_id: str) -> Optional[int]:
        """Находит номер строки в индексе по ID сущности"""
        if not os.path.exists(index_file_path):
            return None
        with open(index_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split('|') 
                if parts and parts[0] == entity_id:
                    return int(parts[1]) 
        return None

    def _update_index(self, index_file: str, entity_id: str, line_number: int) -> None:
        """Обновляет индексный файл"""
        index_entries = []
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                index_entries = [line.strip().split('|') for line in f if line.strip()] 
        
        index_entries = [entry for entry in index_entries if entry[0] != entity_id]
        
        index_entries.append([entity_id, str(line_number)]) 
        
        index_entries.sort(key=lambda x: x[0]) 
        
        with open(index_file, 'w') as f:
            for entry in index_entries:
                f.write(f"{entry[0]}|{entry[1]}\n") 

    def add_model(self, model: Model) -> Model:
        """Добавляет модель автомобиля"""
        self._write_record_and_update_index(self.models_file, self.models_index_file, str(model.id), self._model_to_string(model))
        return model

    def add_car(self, car: Car) -> Car:
        """Добавляет автомобиль"""
        self._write_record_and_update_index(self.cars_file, self.cars_index_file, car.vin, self._car_to_string(car))
        return car

    def add_sale(self, sale: Sale) -> Sale:
        """Добавляет продажу (альтернативный метод для sell_car)"""
        self._write_record_and_update_index(self.sales_file, self.sales_index_file, sale.sales_number, self._sale_to_string(sale))

        car_to_update = self._find_car_by_vin(sale.car_vin) 
        if car_to_update:
            car_to_update.status = CarStatus.sold 
            self._update_car_status_or_data(car_to_update)
        else:
            raise ValueError(f"Автомобиль с VIN {sale.car_vin} не найден для обновления статуса.")
        return sale

    def get_cars(self, status: CarStatus) -> List[Car]:
        """Получает список автомобилей по статусу"""
        cars = []
        if not os.path.exists(self.cars_file): 
            return []
        
        with open(self.cars_file, 'r') as data_file:
            for line in data_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    car = self._string_to_car(line) 
                    if car.status == status:
                        cars.append(car)
                except ValueError:
                    continue
        return cars

    def get_car_info(self, vin: str) -> Optional[CarFullInfo]:
        """Получает полную информацию об автомобиле"""
        car = self._find_car_by_vin(vin)
        if not car:
            raise ValueError(f"Автомобиль с VIN {vin} не найден.")

        model = self._get_model_by_id(car.model) 
        if not model:
            return None

        sale_info = None
        if car.status == CarStatus.sold: 
            sale_info = self._get_sale_by_car_id(vin) 

        return CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price, 
            date_start=car.date_start, 
            status=car.status,
            sales_date=sale_info.sales_date if sale_info else None, 
            sales_cost=sale_info.cost if sale_info else None 
        )

    def update_vin(self, vin: str, new_vin: str) -> Car:
        car = self._find_car_by_vin(vin)
        if not car:
            raise ValueError(f"Автомобиль с VIN {vin} не найден.")
    
    # Проверяем, не существует ли уже автомобиль с новым VIN
        if self._find_car_by_vin(new_vin):
            raise ValueError(f"Автомобиль с VIN {new_vin} уже существует.")

    # Создаем новую запись автомобиля
        updated_car = Car(
            vin=new_vin,
            model=car.model,
            price=car.price,
            date_start=car.date_start,
            status=car.status
        )

    # Удаляем старую запись
        self._remove_record_from_file(self.cars_file, vin)
    
    # Добавляем новую запись
        self.add_car(updated_car)

    # Обновляем ссылки в продажах
        self._update_references_in_sales(vin, new_vin)

    # Возвращаем обновленный автомобиль
        return updated_car
    
    def _remove_record_from_file(self, file_path: str, entity_id: str) -> None:
        """Удаляет запись из файла"""
        old_data_and_line_number = self._get_entity_data_and_line_number(file_path, entity_id)
        if old_data_and_line_number is None:
            return 
        
        _, line_number = old_data_and_line_number
        
        seek_position = line_number * LINE_RECORD_LENGTH
        with open(file_path, 'r+') as f:
            f.seek(seek_position)
            f.write(' ' * RECORD_LENGTH + '\n') 
            f.flush()
        
        self._remove_from_index(self._get_index_file_path(file_path), entity_id)

    def _remove_from_index(self, index_file_path: str, entity_id: str) -> None:
        """Удаляет запись из индекса"""
        index_entries = []
        if os.path.exists(index_file_path):
            with open(index_file_path, 'r') as f:
                index_entries = [line.strip().split('|') for line in f if line.strip()] 
        
        new_index_content = [entry for entry in index_entries if entry[0] != entity_id]
        
        new_index_content.sort(key=lambda x: x[0])
        with open(index_file_path, 'w') as f:
            for entry in new_index_content:
                f.write(f"{entry[0]}|{entry[1]}\n")

    def _update_references_in_sales(self, old_vin: str, new_vin: str) -> None:
        """Обновляет ссылки на VIN в продажах"""
        temp_file = os.path.join(self.root_directory_path, "sales.tmp")
        sales_updated = False
        
        with open(self.sales_file, 'r') as infile, \
                open(temp_file, 'w') as outfile:
            for line in infile:
                if not line.strip(): 
                    outfile.write(line)
                    continue
                
                try:
                    sale_obj = self._string_to_sale(line)
                except ValueError:
                    outfile.write(line) 
                    continue

                if sale_obj.car_vin == old_vin:
                    sale_obj.car_vin = new_vin
                    outfile.write(self._sale_to_string(sale_obj) + '\n') 
                    sales_updated = True
                else:
                    outfile.write(self._sale_to_string(sale_obj) + '\n') 
        if sales_updated:
            os.replace(temp_file, self.sales_file)
            self._rebuild_sales_index()
        else:
            os.remove(temp_file)

    def _rebuild_sales_index(self):
        """Перестраивает индекс продаж"""
        if not os.path.exists(self.sales_file):
            return
        index_entries = []
        with open(self.sales_file, 'r') as f:
            current_line_number = 0
            for line in f:
                if line.strip(): 
                    try:
                        sale = self._string_to_sale(line)
                        index_entries.append([sale.sales_number, str(current_line_number)])
                    except ValueError:
                        pass 
                current_line_number += 1 
        index_entries.sort(key=lambda x: x[0])
        with open(self.sales_index_file, 'w') as f:
            for entry in index_entries:
                f.write(f"{entry[0]}|{entry[1]}\n")

    def _get_car_by_vin(self, vin: str) -> Optional[Car]:
        """Получает автомобиль по VIN (внутренний метод)"""
        line_number = self._find_line_number_in_index(self.cars_index_file, vin)
        if line_number is None:
            return None
        
        seek_position = line_number * LINE_RECORD_LENGTH
        with open(self.cars_file, 'r') as f:
            f.seek(seek_position)
            line_content = f.read(RECORD_LENGTH).strip()
            if not line_content: 
                return None
            try:
                return self._string_to_car(line_content)
            except (ValueError, IndexError):
                return None

    def _get_model_by_id(self, model_id: int) -> Optional[Model]:
        """Получает модель по ID"""
        line_number = self._find_line_number_in_index(self.models_index_file, str(model_id))
        if line_number is None:
            return None
        
        seek_position = line_number * LINE_RECORD_LENGTH
        with open(self.models_file, 'r') as f:
            f.seek(seek_position)
            line_content = f.read(RECORD_LENGTH).strip()
            if not line_content: 
                return None
            try:
                return self._string_to_model(line_content)
            except (ValueError, IndexError, TypeError):
                return None

    def _get_sale_by_car_id(self, car_id: str) -> Optional[Sale]:
        """Получает продажу по VIN автомобиля"""
        if not os.path.exists(self.sales_file):
            return None
        with open(self.sales_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    sale = self._string_to_sale(line) 
                    if sale.car_vin == car_id: 
                        return sale
                except (ValueError, IndexError):
                    continue
        return None

    def revert_sale(self, sales_number: str) -> Car:
        """Отменяет продажу"""
        sale_info_found = None
        car_vin_from_sale = None 
        temp_file = os.path.join(self.root_directory_path, "sales_temp.txt")

        with open(self.sales_file, 'r') as infile, open(temp_file, 'w') as outfile:
            for line in infile:
                if not line.strip():
                    outfile.write(line)
                    continue
                
                try:
                    sale_obj = self._string_to_sale(line)
                except ValueError:
                    outfile.write(line) 
                    continue

                if sale_obj.sales_number == sales_number: 
                    sale_info_found = sale_obj
                    car_vin_from_sale = sale_info_found.car_vin 
                else:
                    outfile.write(self._sale_to_string(sale_obj) + '\n') 

        if not sale_info_found:
            os.remove(temp_file)
            raise ValueError(f"Продажа с номером {sales_number} не найдена")

        os.replace(temp_file, self.sales_file)
        self._rebuild_sales_index()

        if car_vin_from_sale: 
            car_to_update = self._find_car_by_vin(car_vin_from_sale)
            if car_to_update:
                car_to_update.status = CarStatus.available 
                self._update_car_status_or_data(car_to_update) 
                return car_to_update
            else:
                raise ValueError(f"Связанный автомобиль с VIN {car_vin_from_sale} не найден для обновления статуса.")
        raise ValueError("VIN автомобиля не найден в записи о продаже")

    def top_models_by_sales(self) -> List[ModelSaleStats]:
        model_sales_count = {}
        car_vin_to_model_id = {}

    # Сначала собираем соответствие VIN -> model_id
        with open(self.cars_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    car = self._string_to_car(line)
                    car_vin_to_model_id[car.vin] = car.model
                except (ValueError, IndexError):
                    continue

    # Затем подсчитываем количество продаж для каждой модели
        with open(self.sales_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    sale = self._string_to_sale(line)
                    model_id = car_vin_to_model_id.get(sale.car_vin)
                    if model_id is not None:
                        model_sales_count[model_id] = model_sales_count.get(model_id, 0) + 1
                except (ValueError, IndexError):
                    continue

    # Сортируем модели по количеству продаж (по убыванию)
        sorted_models = sorted(
            model_sales_count.items(),
            key=lambda item: (-item[1], self._get_model_price(item[0]))
        )

    # Берем топ-3 модели
        result = []
        for model_id, sales_count in sorted_models[:3]:
            model = self._get_model_by_id(model_id)
            if model:
                result.append(ModelSaleStats(
                    car_model_name=model.name,
                    brand=model.brand,
                    sales_count=sales_count
                ))

        return result

    def _get_model_price(self, model_id: int) -> float:
        """Получает цену модели по ID"""
        model = self._get_model_by_id(model_id)
        return getattr(model, 'price', 0.0) if model else 0.0