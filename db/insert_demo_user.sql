-- Insert the user 'mefaloo' with password '010101'
-- IMPORTANT: In production, use a proper password hash (e.g., bcrypt).
-- Here, for demo purposes, we store the plain text hash.

-- Replace 'your_database' with your actual database name if needed.

INSERT INTO users (username, email, password_hash)
VALUES (
  'mefaloo',
  'mefaloo@example.com',
  '$2y$10$Vh42sIXqE0i5GzagxR1C1OuoT.Dw3e2KjtUq8Dh8QmY0YbH5z6a/6'
);

-- The password_hash above is a bcrypt hash for '010101'.
-- If your backend uses a different hashing algorithm, adjust accordingly.