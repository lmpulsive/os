generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = "file:./dev.db"
}

model User {
  id            String             @id @default(uuid())
  name          String
  email         String             @unique
  createdAt     DateTime           @default(now())
  updatedAt     DateTime           @updatedAt
  entitlements  UserEntitlement[]
  sessions      GameplaySession[]
  purchases     Purchase[]
  admin         Admin?             @relation(fields: [id], references: [userId])
}

model Song {
  id              String             @id @default(uuid())
  title           String
  artist          String
  bpm             Int
  durationSeconds Int
  beatmapJson     Json
  audioPath       String
  coverPath       String?
  version         String             @default("1.0")
  isPublished     Boolean            @default(false)
  createdAt       DateTime           @default(now())
  updatedAt       DateTime           @updatedAt
  entitlements    UserEntitlement[]
  sessions        GameplaySession[]
  purchases       Purchase[]
}

model UserEntitlement {
  userId     String
  songId     String
  source     EntitlementSource
  grantedAt  DateTime             @default(now())

  user       User                @relation(fields: [userId], references: [id])
  song       Song                @relation(fields: [songId], references: [id])

  @@id([userId, songId])
}

model GameplaySession {
  id             String             @id @default(uuid())
  userId         String
  songId         String
  songVersion    String
  clientVersion  String
  startedAt      DateTime           @default(now())
  endedAt        DateTime?
  deviceInfo     String?
  isSynced       Boolean            @default(false)

  user           User               @relation(fields: [userId], references: [id])
  song           Song               @relation(fields: [songId], references: [id])
  performance    PerformanceMetric?
}

model PerformanceMetric {
  sessionId    String             @id
  score        Int
  accuracy     Float
  maxCombo     Int?
  modifiers    Json?
  submittedAt  DateTime           @default(now())
  replayHash   String?
  signature    String?

  session      GameplaySession    @relation(fields: [sessionId], references: [id])
}

model Purchase {
  id                String         @id @default(uuid())
  userId            String
  songId            String
  priceCents        Int
  currency          String         @default("USD")
  paymentProcessor  String?
  paymentReference  String?
  purchasedAt       DateTime       @default(now())
  refunded          Boolean        @default(false)

  user              User           @relation(fields: [userId], references: [id])
  song              Song           @relation(fields: [songId], references: [id])
}

model Admin {
  id         String               @id @default(uuid())
  userId     String               @unique
  role       AdminRole
  grantedAt  DateTime             @default(now())

  user       User                 @relation(fields: [userId], references: [id])
}

enum EntitlementSource {
  purchase
  promo
  admin
  default
}

enum AdminRole {
  editor
  publisher
  superadmin
}
