/* SPDX-License-Identifier: GPL-3.0-or-later
 * Copyright © 2019 by The qTox Project Contributors
 * Copyright © 2024-2026 The TokTok team.
 */

#pragma once

#include <QHash>

template <typename T>
struct Addable
{
    T operator+(const T& other) const
    {
        return static_cast<const T&>(*this).get() + other.get();
    }
};

template <typename T, typename Underlying>
struct UnderlyingAddable
{
protected:
    UnderlyingAddable() = default;

public:
    T operator+(const Underlying& other) const
    {
        return T(static_cast<const T&>(*this).get() + other);
    }
};

template <typename T, typename Underlying>
struct UnitlessSubtractable
{
protected:
    UnitlessSubtractable() = default;

public:
    T operator-(const Underlying& other) const
    {
        return T(static_cast<const T&>(*this).get() - other);
    }

    Underlying operator-(const T& other) const
    {
        return static_cast<const T&>(*this).get() - other.get();
    }
};

template <typename T, typename>
struct Incrementable
{
protected:
    Incrementable() = default;

public:
    T& operator++()
    {
        auto& underlying = static_cast<T&>(*this).get();
        ++underlying;
        return static_cast<T&>(*this);
    }

    T operator++(int)
    {
        auto ret = T(static_cast<const T&>(*this));
        ++(*this);
        return ret;
    }
};


template <typename T, typename>
struct EqualityComparable
{
protected:
    EqualityComparable() = default;

public:
    // Non-member hidden friend: avoids C++20 reversed-argument ambiguity
    // between operator== and operator!=. C++20 synthesizes != from == automatically.
    friend bool operator==(const T& lhs, const T& rhs)
    {
        return lhs.get() == rhs.get();
    }
};

template <typename T, typename Underlying>
struct Hashable
{
    friend uint qHash(const Hashable<T, Underlying>& key, uint seed = 0)
    {
        return qHash(static_cast<const T&>(*key).get(), seed);
    }
};

template <typename T, typename Underlying>
struct Orderable : EqualityComparable<T, Underlying>
{
protected:
    Orderable() = default;

public:
    bool operator<(const T& rhs) const
    {
        return static_cast<const T&>(*this).get() < rhs.get();
    }
    bool operator>(const T& rhs) const
    {
        return static_cast<const T&>(*this).get() > rhs.get();
    }
    bool operator>=(const T& rhs) const
    {
        return static_cast<const T&>(*this).get() >= rhs.get();
    }
    bool operator<=(const T& rhs) const
    {
        return static_cast<const T&>(*this).get() <= rhs.get();
    }
};


/**
 * This class facilitates creating a named class which wraps underlying POD,
 * avoiding implicit casts and arithmetic of the underlying data.
 * Usage: Declare named type with arbitrary tag, then hook up Qt metatype for use
 * in signals/slots. For queued connections, registering the metatype is also
 * required before the type is used.
 *
 * <code>
 *   using ReceiptNum = NamedType<uint32_t, struct ReceiptNumTag>;
 *   Q_DECLARE_METATYPE(ReceiptNum)
 *   qRegisterMetaType<ReceiptNum>();
 * </code>
 *
 * The value member is always initialized to 0.
 */
template <typename T, typename Tag, template <typename, typename> class... Properties>
class NamedType : public Properties<NamedType<T, Tag, Properties...>, T>...
{
public:
    using UnderlyingType = T;

    NamedType() = default;
    explicit NamedType(const T& value)
        : value_(value)
    {
    }
    T& get()
    {
        return value_;
    }
    const T& get() const
    {
        return value_;
    }

private:
    T value_{0};
};

template <typename T, typename Tag, template <typename, typename> class... Properties>
uint qHash(const NamedType<T, Tag, Properties...>& key, uint seed = 0)
{
    return static_cast<uint>(qHash(key.get(), seed));
}
