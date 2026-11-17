import React from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  ScrollView,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Shirt, Sparkles, Gamepad2, Plane } from 'lucide-react-native';
import type { LucideIcon } from 'lucide-react-native';

type Industry = {
  id: string;
  name: string;
  match: number; // 0-100
  Icon: LucideIcon;
};

const INDUSTRIES: Industry[] = [
  { id: 'moda', name: 'Moda y Ropa', match: 92, Icon: Shirt },
  { id: 'belleza', name: 'Maquillaje y Belleza', match: 85, Icon: Sparkles },
  { id: 'tech', name: 'Videojuegos y Tecnología', match: 60, Icon: Gamepad2 },
  { id: 'viajes', name: 'Viajes y Turismo', match: 45, Icon: Plane },
];

const colors = {
  bg: '#F9FAFB',
  card: '#FFFFFF',
  border: '#E5E7EB',
  title: '#111827',
  muted: '#6B7280',
  blue: '#2563EB',
  blueSoft: '#EFF6FF',
  green: '#25EB9F',
  slate: '#6F7E9D',
  white: '#FFFFFF',
};

// Si usas @expo-google-fonts/inter, reemplaza por 'Inter_700Bold', 'Inter_600SemiBold', etc.
const fonts = {
  regular: undefined as string | undefined,
  semibold: undefined as string | undefined,
  bold: undefined as string | undefined,
};

function IndustryCard({ name, match, Icon }: Industry) {
  return (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <View style={styles.iconBox}>
          <Icon size={20} color={colors.blue} />
        </View>
        <Text style={styles.cardName}>{name}</Text>
        <Text style={styles.cardPercent}>{match}%</Text>
      </View>

      <View style={styles.matchBlock}>
        <View style={styles.matchRow}>
          <Text style={styles.matchLabel}>Match</Text>
          <Text style={styles.matchValue}>{match}%</Text>
        </View>
        <View style={styles.track}>
          <View style={[styles.fill, { width: `${match}%` }]} />
        </View>
      </View>
    </View>
  );
}

type Props = {
  onContact?: () => void;
  onCancel?: () => void;
};

export default function SectoresCompatiblesScreen({
  onContact,
  onCancel,
}: Props) {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <StatusBar barStyle="dark-content"/>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Sectores Compatibles</Text>
          <Text style={styles.subtitle}>
            Prioriza las industrias con mayor afinidad para tu campaña.
          </Text>
        </View>

        <View style={styles.list}>
          {INDUSTRIES.map((item) => (
            <IndustryCard key={item.id} {...item} />
          ))}
        </View>

        <View style={styles.actions}>
          <Pressable
            onPress={onContact}
            style={({ pressed }) => [
              styles.button,
              { backgroundColor: colors.green },
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.buttonText}>Contactar Influencer</Text>
          </Pressable>

          <Pressable
            onPress={onCancel}
            style={({ pressed }) => [
              styles.button,
              { backgroundColor: colors.slate },
              pressed && styles.pressed,
            ]}
          >
            <Text style={styles.buttonText}>Cancelar Contratación</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 32,
    gap: 24,
  },
  header: { gap: 8 },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.title,
    fontFamily: fonts.bold,
  },
  subtitle: {
    fontSize: 14,
    color: colors.muted,
    fontFamily: fonts.regular,
  },
  list: { gap: 16 },
  card: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    padding: 16,
    gap: 12,
  },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.blueSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardName: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: colors.title,
    fontFamily: fonts.semibold,
  },
  cardPercent: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.blue,
    fontFamily: fonts.bold,
  },
  matchBlock: { gap: 6 },
  matchRow: { flexDirection: 'row', justifyContent: 'space-between' },
  matchLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.muted,
    fontFamily: fonts.semibold,
  },
  matchValue: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.blue,
    fontFamily: fonts.semibold,
  },
  track: {
    height: 8,
    borderRadius: 999,
    backgroundColor: colors.border,
    overflow: 'hidden',
  },
  fill: { height: 8, borderRadius: 999, backgroundColor: colors.blue },
  actions: { gap: 24, marginTop: 'auto' },
  button: {
    height: 63,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.white,
    fontFamily: fonts.semibold,
  },
  pressed: { opacity: 0.85 },
});