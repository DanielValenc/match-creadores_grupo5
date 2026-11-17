import React, { useEffect } from "react";
import { View, Text, StyleSheet, StatusBar, Pressable } from "react-native";
import Logo from "../components/Logo";
import { colors } from "../theme";

type Props = { onDone: () => void };

export default function FrontScreen({ onDone }: Props) {
  useEffect(() => {
    const t = setTimeout(onDone, 2000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Pressable style={styles.container} onPress={onDone}>
      <StatusBar barStyle="light-content" />
      <Logo size={96} />
      <Text style={styles.title}>TrueMatch AI</Text>
      <Text style={styles.tagline}>Auditoría y Psicología de Creadores</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.navy,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 24,
  },
  title: {
    marginTop: 28,
    fontSize: 34,
    fontWeight: "700",
    color: colors.white,
    textAlign: "center",
  },
  tagline: {
    marginTop: 14,
    fontSize: 13,
    lineHeight: 20,
    color: colors.mist,
    textAlign: "center",
  },
});
