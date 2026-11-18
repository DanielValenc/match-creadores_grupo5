import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, StatusBar, Animated, Easing } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, LinearGradient, Stop } from 'react-native-svg';
import Logo from '../components/Logo';
import PrimaryButton from '../components/PrimaryButton';
import { useCreatorAnalysis } from '../hooks/useCreatorAnalysis';
import { colors } from '../theme';

type Props = { usuario: string; onDone: () => void; onBack: () => void };

const STEPS = [
  'Leyendo videos recientes de TikTok...',
  'Aplicando Ley de Benford...',
  'Analizando rasgos Big Five (IA)...',
];

const R = 83;
const C = 2 * Math.PI * R;

export default function LoadingScreen({ usuario, onDone, onBack }: Props) {
  const [active, setActive] = useState(0);
  const spin = useRef(new Animated.Value(0)).current;
  const { status, errorMessage, analyze } = useCreatorAnalysis();
  const failed = status === 'error';

  // Lanza el análisis real y navega al Dashboard solo cuando termina bien.
  useEffect(() => {
    let mounted = true;
    analyze(usuario).then((ok) => {
      if (ok && mounted) onDone();
    });
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usuario]);

  useEffect(() => {
    Animated.loop(
      Animated.timing(spin, {
        toValue: 1,
        duration: 1600,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
    const t1 = setInterval(
      () => setActive((a) => Math.min(a + 1, STEPS.length - 1)),
      1500
    );
    return () => {
      clearInterval(t1);
      spin.stopAnimation();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const rotate = spin.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" />
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Analizando a</Text>
          <View style={styles.userBlock}>
            <Text style={styles.userText}>@{usuario}</Text>
          </View>
        </View>

        {failed ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorTitle}>No se pudo completar el análisis</Text>
            <Text style={styles.errorText}>{errorMessage}</Text>
          </View>
        ) : (
        <View style={styles.progress}>
          <View style={styles.spinner}>
            <Animated.View style={[StyleSheet.absoluteFill, { transform: [{ rotate }] }]}>
              <Svg width={180} height={180} viewBox="0 0 180 180">
                <Defs>
                  <LinearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                    <Stop offset="0" stopColor="#A5ECF5" />
                    <Stop offset="0.5" stopColor="#10B981" />
                    <Stop offset="1" stopColor="#2563EB" />
                  </LinearGradient>
                </Defs>
                <Circle cx={90} cy={90} r={R} stroke="#1B2538" strokeWidth={14} fill="none" />
                <Circle
                  cx={90}
                  cy={90}
                  r={R}
                  stroke="url(#g)"
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
            {STEPS.map((s, i) => (
              <View key={s} style={styles.step}>
                <View style={styles.dot} />
                <Text
                  style={[styles.stepText, i === active && { color: colors.white }]}
                >
                  {s}
                </Text>
              </View>
            ))}
          </View>
        </View>
        )}

        <View style={styles.flex} />
        {failed ? (
          <PrimaryButton label="Volver" onPress={onBack} />
        ) : (
          <Text style={styles.footer}>
            Si no hay un análisis guardado, puede tardar varios minutos...
          </Text>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.navy },
  flex: { flex: 1 },
  content: { flex: 1, paddingHorizontal: 24, paddingTop: 40, paddingBottom: 40, gap: 32 },
  header: { gap: 12 },
  title: { fontSize: 28, fontWeight: '700', color: colors.white },
  userBlock: {
    alignSelf: 'flex-start',
    backgroundColor: colors.navyCard,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  userText: { fontSize: 16, fontWeight: '600', color: colors.cyan },
  progress: { alignItems: 'center', gap: 24 },
  spinner: { width: 180, height: 180, alignItems: 'center', justifyContent: 'center' },
  steps: { alignSelf: 'stretch', gap: 12 },
  step: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: colors.cyan },
  stepText: { flex: 1, fontSize: 14, color: colors.mist },
  errorBox: {
    backgroundColor: colors.navyCard,
    borderRadius: 16,
    padding: 16,
    gap: 8,
  },
  errorTitle: { fontSize: 16, fontWeight: '600', color: colors.white },
  errorText: { fontSize: 14, lineHeight: 20, color: colors.mist },
  footer: { fontSize: 13, color: colors.mist, textAlign: 'center' },
});