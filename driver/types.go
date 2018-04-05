package driver

type Type uint

const (
	UNKNOWN = iota
	BOOLEAN
	FLOAT64
	INT64
	UINT64
	STRING
	TRIPLE
	ARRAY_BOOLEAN
	ARRAY_FLOAT64
	ARRAY_INT64
	ARRAY_UINT64
	ARRAY_STRING
	ARRAY_TRIPLE
)

func TypeFromString(s string) Type {
	switch s {
	case "bool", "boolean":
		return BOOLEAN
	case "float64", "float", "double":
		return FLOAT64
	case "int64", "int":
		return INT64
	case "uint64", "uint":
		return UINT64
	case "string":
		return STRING
	case "triple":
		return TRIPLE
	case "[]bool", "[]boolean":
		return ARRAY_BOOLEAN
	case "[]float64", "[]float", "[]double":
		return ARRAY_FLOAT64
	case "[]int64", "[]int":
		return ARRAY_INT64
	case "[]uint64", "[]uint":
		return ARRAY_UINT64
	case "[]string":
		return ARRAY_STRING
	case "[]triple":
		return ARRAY_TRIPLE
	default:
		return UNKNOWN
	}
}
