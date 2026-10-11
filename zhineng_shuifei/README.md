# 沃野云枢：独立式水肥分析决策平台

本软件独立于水肥一体化机运行，不连接硬件接口，不向设备自动发送数据，也不会生成虚假的自动执行回执。完整工作方式为：

`人工/批量录入监测数据 -> 雨城区三日天气 -> 需求预测 -> 水肥决策 -> 生成设备参数 -> 人工传达给硬件操作人员 -> 人工登记实际执行量 -> 报告留痕`

## VS Code 运行

1. 在 VS Code 中打开文件夹 `C:\Users\D1782\Desktop\xiangmu\zhineng_shuifei`。
2. 选择左侧“运行和调试”，运行“启动沃野云枢”。
3. 浏览器打开 `http://127.0.0.1:5000`。

也可以在终端运行：

```powershell
cd backend
python -m pip install -r requirements.txt
python yingyong.py
```

演示账号：`admin`，密码：`123456`。

系统每次打开会先显示登录页；勾选“记住密码”只会在下次打开时预填账号和密码，不会自动跳过登录。

## 功能范围

- 登录页：账号、密码、登录、记住密码；
- 首页：今日监测、预警和建议数，当前生产状态及六类趋势图；
- 基础信息：作物、土壤、设备、肥料，包含油橄榄五个生育阶段参数；
- 数据监测：手动录入、Excel/CSV 批量导入、日期筛选；
- 天气分析：雅安市雨城区未来三日温度、降雨、湿度与蒸散分析；
- 预测分析：1-3 日范围、是否采用天气、需水/需肥/湿度对比与旱情分析；
- 水肥决策：水分与肥力评估、建议量、泵运行参数、依据和历史趋势；
- 报告中心：报告列表、全中文字段详情及浏览器打印/另存为 PDF；
- 人工协同：不展示设备状态，只保留操作单生成、人工确认和实际执行量登记；
- 系统管理：预警阈值和操作日志。

## 病虫害模型接入

病虫害页面已经接入两个 GitHub 项目的可替换接口：

- [ezer22/olive-disease-detection](https://github.com/ezer22/olive-disease-detection)：使用其油橄榄 YOLOv11 的 `data.yaml` 类别组织和推理约定。把经过油橄榄数据训练的 `best.pt` 放到 `backend/models/pest_yolo/best.pt`，并安装可选依赖后，页面会自动输出检测框和置信度。
- [kozodoi/Kaggle_Leaf_Disease_Classification](https://github.com/kozodoi/Kaggle_Leaf_Disease_Classification)：只迁移 CNN 局部纹理与 Transformer 全局上下文融合思路。该仓库默认数据和权重是木薯叶病害，不能直接作为油橄榄诊断模型；油橄榄双分支权重完成训练后再通过 `OLIVE_HYBRID_WEIGHTS` 接入。

可选模型依赖单独列在 `backend/requirements-ml.txt`，基础环境不安装 PyTorch/Ultralytics 也能正常运行。权重路径也可以通过 `backend/.env` 中的 `OLIVE_YOLO_WEIGHTS`、`OLIVE_YOLO_DATA` 和 `OLIVE_HYBRID_WEIGHTS` 配置。模型未配置或加载失败时，接口会明确返回规则降级状态，不伪造论文精度或病种结果。

### 训练数据收集与标注

实际应用应优先采集雅安、西昌及目标油橄榄园的本地样本：健康叶、孔雀斑病、炭疽病、虫害、缺素、药害和机械损伤，并覆盖晴天/阴天、叶片正反面、不同距离、品种和病害严重程度。每张图保留地点、日期、品种、病种、严重程度、天气湿度和专家复核字段。

公开数据可用于预训练和补充：

- [CNN_olive_dataset](https://github.com/sinanuguz/CNN_olive_dataset)：健康、橄榄孔雀斑和 Aculus olearius 等分类图像；若用于 YOLO，需要重新画检测框。
- [OliveLeafDiseaseDatasetTacna](https://github.com/ichaparroc/OliveLeafDiseaseDatasetTacna)：Fumagina、Virosis 和营养缺乏等油橄榄叶图像；使用前确认数据许可。
- [olive_disease_paper_reimplementation](https://github.com/MohamedKhalidmk/olive_disease_paper_reimplementation)：可参考数据组织和分类训练流程，不能默认其权重适用于本软件。

YOLO 目标检测需要用 Roboflow、CVAT、Label Studio 或 LabelImg 标注，格式为每行 `class_id x_center y_center width height`，坐标归一化到 0-1，并按训练/验证/测试集分离。建议每个类别至少准备数百张经过专家确认的图片，且测试集按地块或采集日期隔离，避免同一叶片泄漏到训练集。

安装真实模型依赖：

```powershell
cd backend
python -m pip install -r requirements-ml.txt
python yingyong.py
```

## 雅安市雨城区天气

点击天气分析页“更新公开天气”后，后端按雨城区中心坐标（约北纬 29.98°、东经 103.00°）读取 Open-Meteo 三日预报并缓存。网络不可用时自动继续使用数据库缓存，页面会显示数据来源和更新时间。公开天气只用于分析演示，正式生产应接入有服务保障的气象源并进行站点校正。

## 数据库

默认使用 `backend/nongye.db`，方便没有数据库环境时直接演示。正式部署建议使用 MySQL 8：

```sql
CREATE DATABASE shuifei CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

启动前设置连接地址，程序会自动执行 [mysql_chushihua.sql](backend/mysql_chushihua.sql)：

```powershell
$env:DATABASE_URL='mysql+pymysql://root:你的密码@127.0.0.1:3306/shuifei'
python backend\yingyong.py
```

## 数据边界

油橄榄需水、需肥和目标湿度为一般栽培规律下的演示参数，不应直接作为农业生产处方。参赛或实地应用前，需要结合具体品种、树龄、土壤实测、灌溉效率和当地农艺试验校准，并由现场人员最终确认。

运行测试：

```powershell
python -m unittest discover -s backend -p "test_*.py" -v
```
