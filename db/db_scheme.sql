CREATE TABLE sqlite_sequence(name,seq)

CREATE TABLE "user_badges" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
   `userId` INTEGER NOT NULL, `badgeId` INTEGER NOT NULL, `date` TEXT NOT NULL,
   `valid` INTEGER NOT NULL, `grantby` INTEGER NOT NULL )

CREATE TABLE "badges" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
  `name` TEXT NOT NULL, `img` TEXT, `desc` TEXT NOT NULL, `effect` INTEGER NOT NULL, `adminawarded` INTEGER NOT NULL )

CREATE TABLE "user" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
  `email` TEXT NOT NULL, `username` TEXT NOT NULL, `rating` INTEGER NOT NULL,
  `creator` INTEGER NOT NULL, `validated` INTEGER NOT NULL )

CREATE TABLE "product" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `name` TEXT NOT NULL, `price` REAL )

CREATE TABLE "contract_temp" ( `to_whom` INTEGER NOT NULL, `product` INTEGER NOT NULL )
CREATE TABLE "contract" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, `buyer`
  INTEGER NOT NULL, `to_whom` INTEGER NOT NULL, `product` INTEGER NOT NULL, `date` INTEGER NOT NULL, `creator` INTEGER NOT NULL )

CREATE VIEW all_list as select date, buyer, to_whom, name product, price, buyer_rating from
(select date, buyer,buyer_rating, username to_whom, product from
  (select date, username buyer, to_whom, product, rating buyer_rating from
    contract join user on contract.buyer=user.id) buyer join user on buyer.to_whom = user.id) transactions
    join product on transactions.product = product.id

CREATE VIEW badges_granted_timeline AS select b.grantId, b.uid, b.username, b.date, b.img, b.badgeName, b.badgeId, b.grantById, user.username, b.valid from
(select grantId, user.id uid, username, date, img, badgeName, badgeId, grantby grantById, valid from (select grantId, userId, badgeId, date, img, badges.name badgeName, grantby, valid from
  (select user_badges.id grantId, user.id userId, date, badgeId, user_badges.grantby grantby, user_badges.valid valid from user join user_badges on user.id=user_badges.userId) a
  join badges on badges.id=a.badgeId) join user on user.id=userId order by date desc) b join user on grantById=user.id
