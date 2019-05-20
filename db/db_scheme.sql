CREATE TABLE sqlite_sequence(name,seq)

CREATE TABLE `user_badges` ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `userId` INTEGER NOT NULL, `badgeId` INTEGER NOT NULL, `date` TEXT NOT NULL )

CREATE TABLE "badges" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `name` TEXT NOT NULL, `img` TEXT, `desc` TEXT NOT NULL, `effect` INTEGER NOT NULL )

CREATE TABLE "user" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
  `email` TEXT NOT NULL, `username` TEXT NOT NULL, `rating` INTEGER NOT NULL,
  `creator` INTEGER NOT NULL, `validated` INTEGER NOT NULL )

CREATE TABLE "product" ( `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, `name` TEXT NOT NULL, `price` REAL )

CREATE TABLE "contract_temp" ( `to_whom` INTEGER NOT NULL, `product` INTEGER NOT NULL )
CREATE TABLE "contract" ( `id` INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, `buyer`
  INTEGER NOT NULL, `seller` INTEGER NOT NULL, `product` INTEGER NOT NULL, `date` INTEGER NOT NULL, `creator` INTEGER NOT NULL )

CREATE VIEW all_list as select date, buyer, seller offer, name product, price, buyer_rating from
(select date, buyer,buyer_rating, username seller, product from
  (select date, username buyer, seller, product, rating buyer_rating from
    contract join user on contract.buyer=user.id) buyer join user on buyer.seller = user.id) transactions
    join product on transactions.product = product.id
