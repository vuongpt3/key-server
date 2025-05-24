const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const { v4: uuidv4 } = require("uuid");

const app = express();
app.use(cors());
app.use(express.json());

mongoose.connect(process.env.MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true });

const keySchema = new mongoose.Schema({
    key: String,
    duration: Number,
    createdAt: { type: Date, default: Date.now },
    deviceId: String
});

const Key = mongoose.model("Key", keySchema);

// Tạo key mới
app.post("/create-key", async (req, res) => {
    const { duration } = req.body;
    const randomCode = uuidv4().split("-")[0].toUpperCase();
    const key = `VIP_${duration}D_${randomCode}`;

    const newKey = new Key({ key, duration });
    await newKey.save();

    res.json({ success: true, key });
});

// Kiểm tra key
app.post("/check-key", async (req, res) => {
    const { key, deviceId } = req.body;
    const foundKey = await Key.findOne({ key });

    if (!foundKey) return res.json({ success: false, message: "Key không tồn tại" });

    const now = new Date();
    const expireDate = new Date(foundKey.createdAt);
    expireDate.setDate(expireDate.getDate() + foundKey.duration);

    if (now > expireDate) return res.json({ success: false, message: "Key đã hết hạn" });

    if (!foundKey.deviceId) {
        foundKey.deviceId = deviceId;
        await foundKey.save();
    }

    if (foundKey.deviceId !== deviceId) return res.json({ success: false, message: "Sai thiết bị" });

    res.json({ success: true, message: "Key hợp lệ" });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server chạy ở cổng ${PORT}`));