"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Model } from "@tensorflow-models/mobilenet";

const CANVAS_WIDTH = 480;
const CANVAS_HEIGHT = 360;
const STROKE_COLOR = "#38bdf8";
const STROKE_WIDTH = 10;

interface GuessResult {
  className: string;
  probability: number;
}

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const isDrawingRef = useRef(false);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const [model, setModel] = useState<Model | null>(null);
  const [loadingModel, setLoadingModel] = useState(true);
  const [guess, setGuess] = useState<GuessResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isGuessing, setIsGuessing] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = STROKE_COLOR;
    ctx.lineWidth = STROKE_WIDTH;
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    ctxRef.current = ctx;
  }, []);

  useEffect(() => {
    let mounted = true;

    const loadModel = async () => {
      try {
        setLoadingModel(true);
        const mobilenet = await import("@tensorflow-models/mobilenet");
        await import("@tensorflow/tfjs");
        if (!mounted) {
          return;
        }
        const loadedModel = await mobilenet.load({ version: 2, alpha: 1 });
        if (!mounted) {
          loadedModel.dispose();
          return;
        }
        setModel(loadedModel);
      } catch (err) {
        console.error(err);
        setError("模型加载失败，请刷新页面重试。");
      } finally {
        if (mounted) {
          setLoadingModel(false);
        }
      }
    };

    loadModel();

    return () => {
      mounted = false;
      setModel((current) => {
        current?.dispose();
        return null;
      });
    };
  }, []);

  const getCanvasPoint = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const scaleX = CANVAS_WIDTH / rect.width;
    const scaleY = CANVAS_HEIGHT / rect.height;
    return {
      x: (event.clientX - rect.left) * scaleX,
      y: (event.clientY - rect.top) * scaleY
    };
  }, []);

  const drawLine = useCallback((from: { x: number; y: number }, to: { x: number; y: number }) => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
  }, []);

  const handlePointerDown = useCallback(
    (event: React.PointerEvent<HTMLCanvasElement>) => {
      event.preventDefault();
      const point = getCanvasPoint(event);
      isDrawingRef.current = true;
      lastPointRef.current = point;
    },
    [getCanvasPoint]
  );

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<HTMLCanvasElement>) => {
      if (!isDrawingRef.current) return;
      event.preventDefault();
      const point = getCanvasPoint(event);
      const lastPoint = lastPointRef.current;
      if (lastPoint) {
        drawLine(lastPoint, point);
      }
      lastPointRef.current = point;
    },
    [drawLine, getCanvasPoint]
  );

  const handlePointerUp = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current) return;
    event.preventDefault();
    isDrawingRef.current = false;
    lastPointRef.current = null;
  }, []);

  const clearCanvas = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    ctx.strokeStyle = STROKE_COLOR;
    setGuess(null);
    setError(null);
  }, []);

  const handleGuess = useCallback(async () => {
    const canvas = canvasRef.current;
    if (!canvas || !model) {
      setError("模型尚未准备好，请稍后再试。");
      return;
    }

    try {
      setIsGuessing(true);
      setError(null);
      setGuess(null);
      const predictions = await model.classify(canvas);
      if (!predictions || predictions.length === 0) {
        setError("我没看懂这幅画，再试一次吧！");
        return;
      }
      const [top] = predictions;
      setGuess({ className: top.className, probability: top.probability });
    } catch (err) {
      console.error(err);
      setError("识别失败，请重试。");
    } finally {
      setIsGuessing(false);
    }
  }, [model]);

  const helperText = useMemo(() => {
    if (error) return error;
    if (guess)
      return `AI 猜测：${guess.className}（置信度 ${(guess.probability * 100).toFixed(1)}%）`;
    if (loadingModel) return "AI 正在热身加载中…";
    if (isGuessing) return "正在识别你的杰作…";
    return "画点什么，然后让 AI 猜一猜吧！";
  }, [error, guess, isGuessing, loadingModel]);

  return (
    <main className="page">
      <div className="card">
        <header className="card__header">
          <h1>你画我猜 · AI 版</h1>
          <p>在画布上描绘你的创意，点击“让 AI 猜猜”看看模型的想法。</p>
        </header>
        <section className="canvas-wrapper">
          <canvas
            ref={canvasRef}
            width={CANVAS_WIDTH}
            height={CANVAS_HEIGHT}
            className="canvas"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            onPointerLeave={handlePointerUp}
          />
        </section>
        <div className="actions">
          <button className="btn btn-secondary" onClick={clearCanvas}>
            清除画布
          </button>
          <button
            className="btn btn-primary"
            onClick={handleGuess}
            disabled={loadingModel || isGuessing}
          >
            让 AI 猜猜
          </button>
        </div>
        <footer className="status" aria-live="polite">
          {helperText}
        </footer>
      </div>
    </main>
  );
}
