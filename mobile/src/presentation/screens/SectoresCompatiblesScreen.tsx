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
import {
  Baby,
  Car,
  Clapperboard,
  Cpu,
  Dumbbell,
  Gamepad2,
  GraduationCap,
  Heart,
  House,
  Leaf,
  PawPrint,
  Plane,
  Shirt,
  Sparkles,
  Tag,
  Utensils,
  Wallet,
} from 'lucide-react-native';
import type { LucideIcon } from 'lucide-react-native';
import { useCreatorAnalysis } from '../hooks/useCreatorAnalysis';
import type { SectorAffinity } from '../../domain/brand-matching/SectorAffinity';

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

// Palabras clave (sin tildes, en minúsculas) → ícono. Gana la primera que aparezca en la categoría.
const CATEGORY_ICONS: readonly [readonly string[], LucideIcon][] = [
  [['finanz', 'emprend', 'banc', 'invers', 'cripto', 'seguro'], Wallet],
  [['videojuego', 'gaming', 'esport'], Gamepad2],
  [['tecnolog', 'gadget', 'software', 'electron'], Cpu],
  [['educa', 'curso', 'aprendiz', 'formacion'], GraduationCap],
  [['moda', 'ropa', 'calzado'], Shirt],
  [['belleza', 'maquillaje', 'cosmetic', 'cuidado personal'], Sparkles],
  [['viaje', 'turismo', 'hotel'], Plane],
  [['deporte', 'fitness', 'gimnasio'], Dumbbell],
  [['comida', 'aliment', 'bebida', 'gastronom', 'restaur'], Utensils],
  [['salud', 'bienestar'], Heart],
  [['hogar', 'decoracion', 'inmobili'], House],
  [['auto', 'motor', 'vehicul'], Car],
  [['entreten', 'cine', 'musica', 'streaming'], Clapperboard],
  [['mascota'], PawPrint],
  [['bebe', 'infantil', 'familia', 'maternidad'], Baby],
  [['sostenib', 'ecolog', 'medio ambiente'], Leaf],
];

function normalizar(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

function iconFor(category: string): LucideIcon {
  const texto = normalizar(category);
  const match = CATEGORY_ICONS.find(([claves]) => claves.some((k) => texto.includes(k)));
  return match ? match[1] : Tag;
}

function SectorCard({ category, reason }: SectorAffinity) {
  const Icon = iconFor(category);
  return (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <View style={styles.iconBox}>
          <Icon size={20} color={colors.blue} />
        </View>
        <Text style={styles.cardName}>{category}</Text>
      </View>
      {reason.trim() !== '' && <Text style={styles.cardReason}>{reason}</Text>}
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
  const { creator } = useCreatorAnalysis();
  const sectores = creator?.sectorAffinities ?? [];

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
            Industrias afines al contenido del creador y el motivo de cada una.
          </Text>
        </View>

        <View style={styles.list}>
          {!creator ? (
            <Text style={styles.empty}>No hay un análisis cargado.</Text>
          ) : sectores.length === 0 ? (
            <Text style={styles.empty}>
              El análisis no identificó sectores afines para este perfil.
            </Text>
          ) : (
            sectores.map((item, i) => (
              <SectorCard key={`${item.category}-${i}`} {...item} />
            ))
          )}
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
  cardReason: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.muted,
    fontFamily: fonts.regular,
  },
  empty: {
    fontSize: 14,
    color: colors.muted,
    fontFamily: fonts.regular,
  },
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
