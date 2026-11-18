import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  StatusBar,
  Animated,
  Easing,
  Pressable,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import Svg, { Circle, Defs, LinearGradient, Stop } from "react-native-svg";

import Logo from "../components/Logo";
import { colors } from "../theme";
import { analizarCreador } from "../api";
import type { Documento } from "../api";

type Props = {
  usuario: string;
  onDone: (datos: Documento) => void;
  onBack?: () => void;
};

const STEPS = [
  "Conectando con TrueMatch AI...",
  "Extrayendo publicaciones de TikTok...",
  "Aplicando auditoría de audiencia...",
  "Analizando rasgos Big Five con IA...",
];

const R = 83;
const C = 2 * Math.PI * R;

export default function LoadingScreen({ usuario, onDone, onBack }: Props) {
  const [active, setActive] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const spin = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();

    const animation = Animated.loop(
      Animated.timing(spin, {
        toValue: 1,
        duration: 1600,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
    );
    animation.start();

    const interval = setInterval(() => {
      setActive((current) => Math.min(current + 1, STEPS.length - 1));
    }, 4500);

    const runAnalysis = async () => {
      setError(null);
      setActive(0);

      try {
        const datos = await analizarCreador(usuario, controller.signal);
        if (!mounted) return;
        onDone(datos);
      } catch (caught) {
        if (!mounted) return;
        setError(
          caught instanceof Error
            ? caught.message
            : "No se pudo completar el análisis.",
        );
      }
    };

    runAnalysis();

    return () => {
      mounted = false;
      controller.abort();
      clearInterval(interval);
      animation.stop();
      spin.stopAnimation();
    };
  }, [usuario, attempt, onDone, spin]);

  const rotate = spin.interpolate({
    inputRange: [0, 1],
    outputRange: ["0deg", "360deg"],
  });

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" />
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>
            {error ? "No se pudo completar el análisis" : "Analizando a"}
          </Text>
          <View style={styles.userBlock}>
            <Text style={styles.userText}>@{usuario}</Text>
          </View>
        </View>

        <View style={styles.progress}>
          <View style={styles.spinner}>
            <Animated.View
              style={[StyleSheet.absoluteFill, { transform: [{ rotate }] }]}
            >
              <Svg width={180} height={180} viewBox="0 0 180 180">
                <Defs>
                  <LinearGradient
                    id="loadingGradient"
                    x1="0"
                    y1="0"
                    x2="1"
                    y2="1"
                  >
                    <Stop offset="0" stopColor="#A5ECF5" />
                    <Stop offset="0.5" stopColor="#10B981" />
                    <Stop offset="1" stopColor="#2563EB" />
                  </LinearGradient>
                </Defs>
                <Circle
                  cx={90}
                  cy={90}
                  r={R}
                  stroke="#1B2538"
                  strokeWidth={14}
                  fill="none"
                />
                <Circle
                  cx={90}
                  cy={90}
                  r={R}
                  stroke="url(#loadingGradient)"
                  strokeWidth={14}
                  fill="none"
                  strokeDasharray={`${C * 0.75} ${C}`}
                  strokeLinecap="round"
                />
              </Svg>
            </Animated.View>
            <Logo size={96} />
          </View>

          <View style={styles.steps}>
            {STEPS.map((step, index) => (
              <View key={step} style={styles.step}>
                <View
                  style={[styles.dot, index <= active && styles.activeDot]}
                />
                <Text
                  style={[
                    styles.stepText,
                    index === active && styles.activeStepText,
                  ]}
                >
                  {step}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorTitle}>Error de conexión o análisis</Text>
            <Text style={styles.errorText}>{error}</Text>
            <Pressable
              onPress={() => setAttempt((value) => value + 1)}
              style={({ pressed }) => [
                styles.retryButton,
                pressed && styles.pressed,
              ]}
            >
              <Text style={styles.retryText}>Reintentar análisis</Text>
            </Pressable>
            {onBack && (
              <Pressable onPress={onBack} style={styles.backButton}>
                <Text style={styles.backText}>Volver</Text>
              </Pressable>
            )}
          </View>
        )}

        <View style={styles.flex} />
        <Text style={styles.footer}>
          {error
            ? "Revisa el backend y vuelve a intentarlo."
            : "El análisis puede tardar varios minutos."}
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.navy },
  flex: { flex: 1 },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 40,
    paddingBottom: 40,
    gap: 32,
  },
  header: { gap: 12 },
  title: { fontSize: 25, fontWeight: "700", color: colors.white },
  userBlock: {
    alignSelf: "flex-start",
    backgroundColor: colors.navyCard,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  userText: { fontSize: 16, fontWeight: "600", color: colors.cyan },
  progress: { alignItems: "center", gap: 24 },
  spinner: {
    width: 180,
    height: 180,
    alignItems: "center",
    justifyContent: "center",
  },
  steps: { alignSelf: "stretch", gap: 12 },
  step: { flexDirection: "row", alignItems: "center", gap: 10 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.mist },
  activeDot: { backgroundColor: colors.cyan },
  stepText: { flex: 1, fontSize: 13, color: colors.mist },
  activeStepText: { color: colors.white },
  errorContainer: {
    backgroundColor: "#3B1F2B",
    padding: 16,
    borderRadius: 12,
    gap: 10,
  },
  errorTitle: { color: "#FCA5A5", fontSize: 15, fontWeight: "700" },
  errorText: { color: "#FEE2E2", fontSize: 13, lineHeight: 19 },
  retryButton: {
    backgroundColor: colors.blue,
    borderRadius: 10,
    padding: 13,
    alignItems: "center",
  },
  retryText: { color: colors.white, fontSize: 14, fontWeight: "700" },
  backButton: { padding: 8, alignItems: "center" },
  backText: { color: colors.mist, fontSize: 13, fontWeight: "600" },
  pressed: { opacity: 0.8 },
  footer: { fontSize: 13, color: colors.mist, textAlign: "center" },
});
